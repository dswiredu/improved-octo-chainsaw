from dagster import IOManager


class NoOpIOManager(IOManager):
    def handle_output(self, context, obj):
        # do nothing — don't write to disk, DB, or memory
        pass

    def load_input(self, context):
        # return nothing — used only if downstream tries to access asset value
        return None
