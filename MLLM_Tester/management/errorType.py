from enum import Enum
class ErrorType(Enum):
	finish=0
	error=1
	ERROR=2
	timeout=3
	roundout=4
	hang=5