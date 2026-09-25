"""Fixed-target TCP relay. No request parsing, DNS lookup or content logging."""
import argparse
import asyncio
import ipaddress

async def main(target):
    ipaddress.IPv4Address(target)
    async def connection(reader, writer):
        upstream=None
        async def copy(src,dst):
            while True:
                data=await asyncio.wait_for(src.read(65536),timeout=180)
                if not data:break
                dst.write(data);await dst.drain()
        try:
            remote,upstream=await asyncio.wait_for(asyncio.open_connection(target,8000),timeout=5)
            tasks=[asyncio.create_task(copy(reader,upstream)),asyncio.create_task(copy(remote,writer))]
            done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            for task in pending:task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
        except (OSError,asyncio.TimeoutError):pass
        finally:
            writer.close()
            if upstream:upstream.close()
    server=await asyncio.start_server(connection,'127.0.0.1',18000,limit=65536)
    async with server:await server.serve_forever()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--target',required=True)
    asyncio.run(main(parser.parse_args().target))
