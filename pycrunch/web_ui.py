import aiohttp
from aiohttp import web


def enable_for_aiohttp(app, engine_directory):
    async def root_handler(request):
        return aiohttp.web.HTTPFound('/ui/index.html')

    async def favicon_handler(request):
        # return aiohttp.web.HTTPFound('/ui/favicon.ico')
        return web.FileResponse(engine_directory.joinpath('web-ui','favicon.ico'))

    app.router.add_route('*', '/ui/', root_handler)
    app.router.add_route('*', '/favicon.ico', favicon_handler)
    app.add_routes([web.static('/ui', engine_directory.joinpath('web-ui'))])
    app.add_routes([web.static('/js', engine_directory.joinpath('web-ui', 'js'))])
    app.add_routes([web.static('/css', engine_directory.joinpath('web-ui', 'css'))])
    app.add_routes([web.static('/fonts', engine_directory.joinpath('web-ui', 'fonts'))])