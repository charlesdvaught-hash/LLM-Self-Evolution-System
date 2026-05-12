"""
Advisor Knowledge Base Loader

This module helps the 0.8B advisor model access documentation.
The advisor can import this to get file paths and content.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Base docs directory
DOCS_DIR = Path(__file__).parent


class AdvisorKnowledgeBase:
    """Knowledge base interface for the 0.8B advisor model."""
    
    def __init__(self):
        """Initialize the knowledge base."""
        self.manifest_path = DOCS_DIR / "KNOWLEDGE_BASE_MANIFEST.json"
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Load the knowledge base manifest."""
        if self.manifest_path.exists():
            with open(self.manifest_path, 'r') as f:
                return json.load(f)
        return {}
    
    def get_guide(self, guide_name: str) -> Optional[Tuple[str, str]]:
        """
        Get a guide file and its description.
        
        Args:
            guide_name: Key from manifest['guides']
            
        Returns:
            Tuple of (file_path, description) or None
        """
        if 'guides' not in self.manifest:
            return None
        
        guide = self.manifest['guides'].get(guide_name)
        if guide:
            path = DOCS_DIR / guide['path']
            return (str(path), guide.get('description', ''))
        return None
    
    def get_reference(self, ref_name: str) -> Optional[Tuple[str, str]]:
        """
        Get a reference file and its description.
        
        Args:
            ref_name: Key from manifest['reference']
            
        Returns:
            Tuple of (file_path, description) or None
        """
        if 'reference' not in self.manifest:
            return None
        
        ref = self.manifest['reference'].get(ref_name)
        if ref:
            path = DOCS_DIR / ref['path']
            return (str(path), ref.get('description', ''))
        return None
    
    def get_quick_answer(self, question: str) -> Optional[Dict]:
        """
        Get quick answer for a common question.
        
        Args:
            question: Key from manifest['quick_answers']
            
        Returns:
            Dict with 'guide', 'reference', 'keywords' or None
        """
        if 'quick_answers' not in self.manifest:
            return None
        
        answer = self.manifest['quick_answers'].get(question)
        if answer:
            # Convert relative paths to full paths
            result = {}
            for key in ['guide', 'reference']:
                if key in answer:
                    result[key] = str(DOCS_DIR / answer[key])
            result['keywords'] = answer.get('keywords', [])
            return result
        return None
    
    def search_by_topic(self, topic: str) -> List[str]:
        """
        Get all files related to a topic.
        
        Args:
            topic: One of: local, merge, models, advanced, architecture
            
        Returns:
            List of file paths
        """
        if 'search_index' not in self.manifest:
            return []
        
        files = self.manifest['search_index'].get(topic, [])
        return [str(DOCS_DIR / f) for f in files]
    
    def get_advisor_prompt(self, prompt_type: str) -> Optional[str]:
        """
        Get advisor guidance for a specific prompt type.
        
        Args:
            prompt_type: One of: recipe_generation, local_model_usage, etc.
            
        Returns:
            Guidance string or None
        """
        if 'advisor_prompts' not in self.manifest:
            return None
        
        return self.manifest['advisor_prompts'].get(prompt_type)
    
    def list_all_guides(self) -> List[Dict]:
        """
        List all available guides with metadata.
        
        Returns:
            List of dicts with 'name', 'path', 'description', 'keywords', 'topics'
        """
        guides = []
        if 'guides' in self.manifest:
            for name, guide_data in self.manifest['guides'].items():
                guide_data['name'] = name
                guide_data['path'] = str(DOCS_DIR / guide_data['path'])
                guides.append(guide_data)
        return guides
    
    def list_all_references(self) -> List[Dict]:
        """
        List all available references with metadata.
        
        Returns:
            List of dicts with 'name', 'path', 'description', 'keywords', 'topics'
        """
        refs = []
        if 'reference' in self.manifest:
            for name, ref_data in self.manifest['reference'].items():
                ref_data['name'] = name
                ref_data['path'] = str(DOCS_DIR / ref_data['path'])
                refs.append(ref_data)
        return refs
    
    def read_file(self, file_path: str) -> Optional[str]:
        """
        Read content from a documentation file.
        
        Args:
            file_path: Path to file (relative to docs/ or absolute)
            
        Returns:
            File content or None if not found
        """
        # Handle relative paths
        if not os.path.isabs(file_path):
            file_path = str(DOCS_DIR / file_path)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        return None
    
    def search_keyword(self, keyword: str) -> List[Dict]:
        """
        Search for documents by keyword.
        
        Args:
            keyword: Search term
            
        Returns:
            List of matching docs with 'name', 'path', 'match_type'
        """
        results = []
        keyword_lower = keyword.lower()
        
        # Search guides
        if 'guides' in self.manifest:
            for name, guide_data in self.manifest['guides'].items():
                keywords = guide_data.get('keywords', [])
                if any(keyword_lower in k.lower() for k in keywords):
                    results.append({
                        'name': name,
                        'path': str(DOCS_DIR / guide_data['path']),
                        'type': 'guide',
                        'match_type': 'keyword'
                    })
        
        # Search references
        if 'reference' in self.manifest:
            for name, ref_data in self.manifest['reference'].items():
                keywords = ref_data.get('keywords', [])
                if any(keyword_lower in k.lower() for k in keywords):
                    results.append({
                        'name': name,
                        'path': str(DOCS_DIR / ref_data['path']),
                        'type': 'reference',
                        'match_type': 'keyword'
                    })
        
        return results


# Convenience functions for common use cases

def get_kb() -> AdvisorKnowledgeBase:
    """Get the knowledge base instance."""
    return AdvisorKnowledgeBase()


def find_guide(guide_name: str) -> Optional[str]:
    """Get path to a guide file."""
    kb = get_kb()
    result = kb.get_guide(guide_name)
    return result[0] if result else None


def find_reference(ref_name: str) -> Optional[str]:
    """Get path to a reference file."""
    kb = get_kb()
    result = kb.get_reference(ref_name)
    return result[0] if result else None


def answer_question(question: str) -> Optional[Dict]:
    """Get quick answer for a common question."""
    kb = get_kb()
    return kb.get_quick_answer(question)


def search_files(topic: str) -> List[str]:
    """Search for files by topic."""
    kb = get_kb()
    return kb.search_by_topic(topic)


# Example usage for advisor:
if __name__ == "__main__":
    kb = get_kb()
    
    print("=== ADVISOR KNOWLEDGE BASE ===\n")
    
    # Example 1: Get a guide
    print("1. Finding LOCAL MODEL guide:")
    result = kb.get_guide('local_models')
    if result:
        print(f"   Path: {result[0]}")
        print(f"   Description: {result[1]}\n")
    
    # Example 2: Quick answer
    print("2. Quick answer for 'how_to_upload_model':")
    answer = kb.get_quick_answer('how_to_upload_model')
    if answer:
        print(f"   Guide: {answer.get('guide')}")
        print(f"   Reference: {answer.get('reference')}\n")
    
    # Example 3: Search by topic
    print("3. Files about 'merge':")
    merge_files = kb.search_by_topic('merge')
    for f in merge_files:
        print(f"   - {f}\n")
    
    # Example 4: List all guides
    print("4. All available guides:")
    for guide in kb.list_all_guides():
        print(f"   - {guide['name']}: {guide['description']}")
