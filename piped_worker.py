from abc import ABCMeta, abstractmethod

class PipedConsumer(metaclass=ABCMeta):
    """Must implement self.push(data)"""
    @abstractmethod
    def push(self, data):
        raise NotImplementedError

class PipedWorker(PipedConsumer):
    """
    Must implement self.push(data). Should start pushing data to its target
    once it starts receiving data.
    """
    target: PipedConsumer
    def set_target(self, target: PipedConsumer):
        self.target = target

class DummyPipedWorker(PipedWorker):
    def push(self, data):
        pass

    def run(self):
        pass