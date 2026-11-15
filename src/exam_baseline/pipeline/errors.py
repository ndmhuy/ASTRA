class StageContractError(Exception):
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage


class PipelineFailure(Exception):
    def __init__(self, stage: str, code: str, message: str):
        super().__init__(message)
        self.stage, self.code = stage, code
