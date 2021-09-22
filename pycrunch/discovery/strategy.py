from pycrunch.discovery.ast_discovery import AstTestDiscovery
# from pycrunch.discovery.simple import SimpleTestDiscovery


def create_test_discovery(root_directory=None, configuration=None):
    return AstTestDiscovery(root_directory, configuration)
    # or
    # return SimpleTestDiscovery(root_directory, configuration)