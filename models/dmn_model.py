from dataclasses import dataclass
from typing import List, Set, Dict, Tuple

@dataclass
class DecisionTable:
    id: str
    name: str
    input_expressions: List[str]
    output_expressions: List[str]
    rules: List[Dict]

@dataclass
class DMNModel:
    """Represents a DMN decision requirement diagram"""
    
    def __init__(self):
        # Store tuples of (id, name) instead of just ids
        self.decisions: Set[Tuple[str, str]] = set()  # D - decision nodes with names
        self.input_data: Set[Tuple[str, str]] = set()  # I - input data nodes with names
        self.business_knowledge: Set[Tuple[str, str]] = set()  # B - business knowledge nodes with names
        self.knowledge_sources: Set[Tuple[str, str]] = set()  # K - knowledge source nodes with names
        
        # Relations
        self.information_requirements: Set[Tuple[str, str]] = set()  # RI ⊆ D∪I×D
        self.knowledge_requirements: Set[Tuple[str, str]] = set()  # RK ⊆ D∪I×D
        self.authority_requirements: Set[Tuple[str, str]] = set()  # RA ⊆ B×D∪B
        
        # Decision Tables
        self.decision_tables: Dict[str, DecisionTable] = {}  # TD - decision tables
        
    def add_decision(self, decision_id: str, name: str) -> None:
        self.decisions.add((decision_id, name or decision_id))
        
    def add_input_data(self, input_id: str, name: str) -> None:
        self.input_data.add((input_id, name or input_id))
        
    def add_business_knowledge(self, knowledge_id: str, name: str) -> None:
        self.business_knowledge.add((knowledge_id, name or knowledge_id))
        
    def add_knowledge_source(self, source_id: str, name: str) -> None:
        self.knowledge_sources.add((source_id, name or source_id))
        
    def add_information_requirement(self, source: str, target: str) -> None:
        self.information_requirements.add((source, target))
        
    def add_knowledge_requirement(self, source: str, target: str) -> None:
        self.knowledge_requirements.add((source, target))
        
    def add_authority_requirement(self, source: str, target: str) -> None:
        self.authority_requirements.add((source, target))
        
    def add_decision_table(self, decision_id: str, table: DecisionTable) -> None:
        self.decision_tables[decision_id] = table
        
    def get_start_decisions(self) -> Set[Tuple[str, str]]:
        """Returns decisions that don't have any incoming information requirements"""
        all_sources = {source for _, source in self.information_requirements}
        return self.decisions - {(source, name) for source, name in self.decisions if source in all_sources}
        
    def get_start_inputs(self) -> Set[str]:
        """Returns input data used by start decisions"""
        start_decisions = self.get_start_decisions()
        start_inputs = set()
        
        for source, target in self.information_requirements:
            if target in start_decisions and source in self.input_data:
                start_inputs.add(source)
                
        return start_inputs
