import os
import json
from dataclasses import dataclass
from typing import List, Union, Optional

@dataclass
class Constant:
    name: str
    value: str

@dataclass
class Column:
    column: str
    index: int
    constants: Optional[Union[Constant, List[Constant]]] = None

@dataclass
class ColumnConfig:
    columns: List[Column]

    @staticmethod
    def from_json(json_str: str) -> 'ColumnConfig':
        data = json.loads(json_str)
        columns = []
        for col in data.get("columns", []):
            constants_data = col.get("constants")
            if isinstance(constants_data, dict):
                constants = Constant(**constants_data)
            elif isinstance(constants_data, list):
                constants = [Constant(**item) for item in constants_data]
            else:
                constants = None

            column = Column(
                column=col["column"],
                index=col["index"],
                constants=constants
            )
            columns.append(column)
        
        return ColumnConfig(columns=columns)
    
def do_on_get_columns(plantilla_file):
    with open(plantilla_file, "r") as file:
        config = ColumnConfig.from_json(file.read())
        '''for col in config.columns:
            print(f"{col.index}. {col.column}")
            if col.constants:
                if isinstance(col.constants, list):
                    for const in col.constants:
                        print(f"  - Constant: {const.name} = {const.value}")
                else:
                    print(f"  - Constant: {col.constants.name} = {col.constants.value}")'''
        return config.columns