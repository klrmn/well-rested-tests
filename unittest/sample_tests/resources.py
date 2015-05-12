import well_rested_unittest


class Resource(object):
    pass


class ResourceA(well_rested_unittest.ReportingTestResourceManager):

    setUpCost = 1
    tearDownCost = 1

    resources = []

    def make(self, dependency_resources):
        return Resource()

    def clean(self, resource):
        pass
ResourceARM = ResourceA()


class ResourceB(well_rested_unittest.ReportingTestResourceManager):

    setUpCost = 2
    tearDownCost = 1

    resources = [
        ('A', ResourceARM),
    ]

    def make(self, dependency_resources):
        return Resource()

    def clean(self, resource):
        pass
ResourceBRM = ResourceB()


class ResourceC(well_rested_unittest.ReportingTestResourceManager):

    setUpCost = 3
    tearDownCost = 1

    resources = [
        ('B', ResourceBRM),
    ]

    def make(self, dependency_resources):
        return Resource()

    def clean(self, resource):
        pass
ResourceCRM = ResourceC()


class CreateFailResource(well_rested_unittest.ReportingTestResourceManager):

    setUpCost = 9
    tearDownCost = 1

    resources = []

    def make(self, dependency_resources):
        self.logger.info('making walla walla')
        raise Exception('walla walla')

    def clean(self, resource):
        self.logger.info('cleaning walla walla')
CreateFailResourceRM = CreateFailResource()


class DestroyFailResource(well_rested_unittest.ReportingTestResourceManager):

    setUpCost = 8
    tearDownCost = 1

    resources = []

    def make(self, dependency_resources):
        self.logger.info('making booga booga')
        return Resource()

    def clean(self, resource):
        self.logger.info('cleaning booga booga')
        raise Exception('booga booga')
DestroyFailResourceRM = DestroyFailResource()
