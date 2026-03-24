import aiohttp
from aiohttp import web


def enable_for_aiohttp(app, package_directory):
    async def root_handler(request):
        return aiohttp.web.HTTPFound('/ui/index.html')

    async def favicon_handler(request):
        # return aiohttp.web.HTTPFound('/ui/favicon.ico')
        return web.FileResponse(package_directory.joinpath('web-ui', 'favicon.ico'))

    """
        This is api to see to know which files are watched right now.
    """

    async def watched_files_handler(request):
        # import later to not mess with the initialization order
        from pycrunch.api.shared import file_watcher

        if not file_watcher._started:
            return web.json_response([])

        return web.json_response(sorted(list(file_watcher.files)))

    app.router.add_route('*', '/ui/', root_handler)
    app.router.add_route('*', '/watched-files/', watched_files_handler)
    app.router.add_route('*', '/favicon.ico', favicon_handler)
    app.add_routes([web.static('/ui', package_directory.joinpath('web-ui'))])
    app.add_routes([web.static('/js', package_directory.joinpath('web-ui', 'js'))])
    app.add_routes([web.static('/css', package_directory.joinpath('web-ui', 'css'))])
    app.add_routes([
        web.static('/fonts', package_directory.joinpath('web-ui', 'fonts'))
    ])
