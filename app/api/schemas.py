from pydantic import BaseModel


class UserProgram(BaseModel):
    source_code : str
    language_id : int
    command_line_arguments: str
