"""Pre-action checks on HOST-owned metadata, never on a model's self-attestation.

This does not grant permission or execute browser actions. Revision comparison
requires a fresh tool observation; fingerprints must include all material values.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Observation:
    page_id: str
    revision: str
    scope_digest: str  # Host-computed digest of purpose, recipient, files and values.

@dataclass(frozen=True)
class Confirmation:
    action: str
    scope_digest: str
    explicit: bool
    used: bool = False

@dataclass(frozen=True)
class Action:
    kind: str
    target: str
    authorized_scope: bool
    effect: str  # read, local-edit, external, unknown

def check(action, observed, current, confirmation=None, *, paused=False,
          target_unique=True, target_visible=True, outcome_unknown=False,
          unchanged_failures=0):
    if paused:return {'allowed':False,'next':'stop','reason':'user_paused'}
    if not action.authorized_scope:return {'allowed':False,'next':'clarify','reason':'outside_scope'}
    if observed!=current or not current.page_id or not current.revision:
        return {'allowed':False,'next':'observe','reason':'stale_observation'}
    if not target_unique or not target_visible or not action.target:
        return {'allowed':False,'next':'observe','reason':'ambiguous_or_hidden_target'}
    if action.kind in ('login','payment','signature','declaration'):
        return {'allowed':False,'next':'handoff','reason':'user_action'}
    if action.kind not in ('navigate','expand','fill','upload','submit','cancel'):
        return {'allowed':False,'next':'observe','reason':'unknown_action'}
    if outcome_unknown:return {'allowed':False,'next':'observe','reason':'check_previous_outcome'}
    if unchanged_failures>=2:return {'allowed':False,'next':'stop','reason':'repeated_failure'}
    if action.effect not in ('read','local-edit','external'):
        return {'allowed':False,'next':'observe','reason':'unknown_effect'}
    external=action.kind in ('upload','submit','cancel') or action.effect=='external'
    if external:
        if not current.scope_digest or confirmation is None or not confirmation.explicit or confirmation.used or confirmation.action!=action.kind or confirmation.scope_digest!=current.scope_digest:
            return {'allowed':False,'next':'confirm','reason':'missing_matching_confirmation'}
    return {'allowed':True,'next':'execute','consume_confirmation':external}
