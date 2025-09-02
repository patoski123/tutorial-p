from appium.webdriver.common.touch_action import TouchAction
from appium.webdriver.common.multi_action import MultiAction


class GestureHelpers:
    """Mobile gesture utilities"""

    def __init__(self, driver):
        self.driver = driver

    def pinch_zoom_in(self, element, scale: float = 2.0):
        """Perform pinch zoom in gesture"""
        action1 = TouchAction(self.driver)
        action2 = TouchAction(self.driver)

        # Implementation for pinch zoom
        multi_action = MultiAction(self.driver)
        # Add specific pinch zoom logic here
        multi_action.perform()

    def long_press_and_drag(self, start_element, end_element):
        """Long press and drag gesture"""
        action = TouchAction(self.driver)
        action.long_press(start_element).move_to(end_element).release()
        action.perform()

    def swipe_element(self, element, direction: str, distance: int = 100):
        """Swipe on specific element"""
        location = element.location
        size = element.size

        start_x = location['x'] + size['width'] // 2
        start_y = location['y'] + size['height'] // 2

        direction_map = {
            'up': (start_x, start_y - distance),
            'down': (start_x, start_y + distance),
            'left': (start_x - distance, start_y),
            'right': (start_x + distance, start_y)
        }

        end_x, end_y = direction_map.get(direction, (start_x, start_y))
        self.driver.swipe(start_x, start_y, end_x, end_y, 1000)