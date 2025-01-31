from typing import Any, Dict, List, Set

from pydantic import validator

from langchain.memory.utils import get_prompt_input_key
from langchain.schema import BaseMemory


class CombinedMemory(BaseMemory):
    """Class for combining multiple memories' data together."""

    memories: List[BaseMemory]
    """For tracking all the memories that should be accessed."""

    @validator("memories")
    def check_repeated_memory_variable(
        cls, value: List[BaseMemory]
    ) -> List[BaseMemory]:
        all_variables: Set[str] = set()
        for val in value:
            overlap = all_variables.intersection(val.memory_variables)
            if overlap:
                raise ValueError(
                    f"The same variables {overlap} are found in multiple"
                    "memory object, which is not allowed by CombinedMemory."
                )
            all_variables |= set(val.memory_variables)

        return value

    @property
    def memory_variables(self) -> List[str]:
        """All the memory variables that this instance provides."""
        """Collected from the all the linked memories."""

        memory_variables = []

        for memory in self.memories:
            memory_variables.extend(memory.memory_variables)

        return memory_variables

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Load all vars from sub-memories."""
        memory_data: Dict[str, Any] = {}

        # Collect vars from all sub-memories
        for memory in self.memories:
            data = memory.load_memory_variables(inputs)
            memory_data = {
                **memory_data,
                **data,
            }

        return memory_data

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context from this session for every memory."""
        # Remove the variables supplied from sub-memories.
        input_nonmemory_variables = set(inputs) - set(self.memory_variables)
        output_nonmemory_variables = set(outputs) - set(self.memory_variables)

        # Save context for all sub-memories
        for memory in self.memories:
            # Add back in the variables supplied from this memory.
            memory_variables = input_nonmemory_variables | (
                            set(inputs) & set(memory.memory_variables))
            memory_inputs = {k : inputs[k] for k in memory_variables}
            memory_variables = output_nonmemory_variables | (
                            set(outputs) & set(memory.memory_variables))
            memory_outputs = {k : outputs[k] for k in memory_variables}

            memory.save_context(memory_inputs, memory_outputs)

    def clear(self) -> None:
        """Clear context from this session for every memory."""
        for memory in self.memories:
            memory.clear()
