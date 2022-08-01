class ElementCountChanged(object):
    """An expectation for checking that an elements has changes.

    locator - used to find the element
    returns the WebElement once the length has changed

    Source: https://sqa.stackexchange.com/a/8701
    """
    def __init__(self, locator, length):
        self.locator = locator
        self.length = length

    def __call__(self, driver):
        element = driver.find_elements(*self.locator)
        element_count = len(element)
        if element_count > self.length:
            return element
        else:
            return False


class CollectionTooLargeException(Exception):
    pass