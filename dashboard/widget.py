class Widget():
    template_name = None

    def get_context_data(self):
        return {}


widgets = []


def register(Widget):
    widgets.append(Widget())
    return Widget
