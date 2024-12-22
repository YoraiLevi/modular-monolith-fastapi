import logging


class Service:
    class Session:
        def __init__(self, service: "Service"):
            logging.debug(f"Session for service {service.service_name} constructed")
            self.service = service

        def __call__(self):
            logging.debug(f"Session for service {self.service.service_name} called")
            return "Session for service " + self.service.service_name

        def __del__(self):
            logging.debug(f"Session for service {self.service.service_name} destroyed")

        def __enter__(self):
            logging.debug(f"Session for service {self.service.service_name} entered")
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            logging.debug(f"Session for service {self.service.service_name} exited")

    def __init__(self, service_name: str):
        logging.debug(f"Service instance {service_name} constructed")
        self.service_name = service_name

    def __call__(self):
        logging.debug(f"Service {self.service_name} called")
        return self.service_name

    def __del__(self):
        logging.debug(f"Service {self.service_name} destroyed")

    def __enter__(self):
        logging.debug(f"Service {self.service_name} entered")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logging.debug(f"Service {self.service_name} exited")

    def session(self):
        return self.Session(self)
