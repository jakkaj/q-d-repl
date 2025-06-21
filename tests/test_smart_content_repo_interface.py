"""
Test the new Repo-based interface for SmartContentService.

This test verifies that the new process(repo) method:
1. Accepts a Repo object parameter
2. Does NOT perform any file I/O operations
3. Updates objects in-place (preserving object references)
4. Returns structured results instead of saving files
"""

import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import networkx as nx

from src.modules.embeddings.models import EmbeddedContent
from src.modules.embeddings.types import ContentType
from src.modules.lfl.structures import Class, FileHierarchy, Function, Method
from src.modules.llm.models import SmartContentResponse
from src.modules.llm.service import LLMService
from src.modules.repo.models import Repo, RepoMetadata
from src.modules.smart_content.service import SmartContentService


class TestSmartContentRepoInterface(unittest.TestCase):
    """Test the new Repo-based interface for SmartContentService."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock graph
        self.graph = nx.DiGraph()
        
        # Create mock LLM service
        self.llm_service = MagicMock(spec=LLMService)
        self.llm_service.config = MagicMock(provider="test")
        
        # Create test content with proper content types
        self.file_content = EmbeddedContent(
            raw_content="# Test file content",
            content_type=ContentType.FILE_CONTENT,
            smart_content=None
        )
        
        self.class_content = EmbeddedContent(
            raw_content="class TestClass:\n    pass",
            content_type=ContentType.CLASS_CONTENT,
            smart_content=None
        )
        
        self.method_content = EmbeddedContent(
            raw_content="def test_method(self):\n    pass",
            content_type=ContentType.METHOD_CONTENT,
            smart_content=None
        )
        
        self.function_content = EmbeddedContent(
            raw_content="def test_function():\n    pass",
            content_type=ContentType.FUNCTION_CONTENT,
            smart_content=None
        )
        
        # Create test structures
        self.method = Method(
            name="test_method",
            node_id="method:test.py:TestClass.test_method",
            content=self.method_content,
            parameters=["self"],
            start_line=2,
            end_line=3
        )
        
        self.test_class = Class(
            name="TestClass",
            node_id="class:test.py:TestClass",
            content=self.class_content,
            methods=[self.method],
            start_line=1,
            end_line=3
        )
        
        self.function = Function(
            name="test_function",
            node_id="function:test.py:test_function",
            content=self.function_content,
            parameters=[],
            start_line=5,
            end_line=6
        )
        
        self.file_hierarchy = FileHierarchy(
            file_path=Path("test.py"),
            language="python",
            classes=[self.test_class],
            functions=[self.function],
            content=self.file_content,
            node_id="file:test.py",
            line_count=10,
            last_processed=datetime.now(),
            filesystem_last_modified=datetime.now()
        )
        
        # Set up parent references
        self.method.parent = self.test_class
        self.test_class.parent = self.file_hierarchy
        self.function.parent = self.file_hierarchy
        
        # Add nodes to graph with proper node data structure
        self.graph.add_node(
            "file:test.py",
            data={"type": "file", "structure_ref": self.file_hierarchy}
        )
        self.graph.add_node(
            "class:test.py:TestClass",
            data={"type": "class", "structure_ref": self.test_class}
        )
        self.graph.add_node(
            "method:test.py:TestClass.test_method",
            data={"type": "method", "structure_ref": self.method}
        )
        self.graph.add_node(
            "function:test.py:test_function",
            data={"type": "function", "structure_ref": self.function}
        )
        
        # Create test repo
        self.repo = Repo(
            file_hierarchies=[self.file_hierarchy],
            metadata=RepoMetadata(name="test_repo"),
            last_loaded=datetime.now()
        )
        
        # Create service instance
        self.service = SmartContentService(
            graph=self.graph,
            llm_service=self.llm_service
        )

    @patch('asyncio.run')
    def test_process_updates_objects_in_place(self, mock_asyncio_run):
        """Test that process() updates objects in-place without file I/O."""
        # Set up mock LLM responses
        mock_response = SmartContentResponse(
            content="This is smart content for the element",
            tokens_used=100,
            model="test-model",
            provider="test"
        )
        mock_asyncio_run.return_value = None
        
        # Mock the LLM service to return smart content
        async def mock_generate_smart_content(*args, **kwargs):
            return mock_response
        
        self.llm_service.generate_smart_content_with_relationships = AsyncMock(
            side_effect=mock_generate_smart_content
        )
        
        # Capture original object IDs to verify they're not replaced
        original_file_id = id(self.file_hierarchy)
        original_class_id = id(self.test_class)
        original_method_id = id(self.method)
        original_function_id = id(self.function)
        
        # Mock _process_element to simulate smart content generation
        async def mock_process_element(element, element_type):
            element.content.smart_content = f"Smart content for {element_type}"
            element.content.smart_content_hash = element.content.raw_content_hash
        
        # Patch asyncio.run in the service module
        original_run = mock_asyncio_run.__wrapped__ if hasattr(mock_asyncio_run, '__wrapped__') else None
        
        def custom_asyncio_run(coro):
            # Run the async mock synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(mock_process_element(
                    coro.cr_frame.f_locals['element'],
                    coro.cr_frame.f_locals['element_type']
                ))
            finally:
                loop.close()
                
        with patch('asyncio.run', side_effect=custom_asyncio_run):
            # Process the repo
            result = self.service.process(self.repo)
        
        # Verify results
        self.assertEqual(result["processed"], 4)  # file, class, method, function
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["total_elements"], 4)
        self.assertEqual(result["elements_by_type"], {
            "file": 1,
            "class": 1,
            "method": 1,
            "function": 1
        })
        
        # Verify objects were updated in-place (same object IDs)
        self.assertEqual(id(self.file_hierarchy), original_file_id)
        self.assertEqual(id(self.test_class), original_class_id)
        self.assertEqual(id(self.method), original_method_id)
        self.assertEqual(id(self.function), original_function_id)
        
        # Verify smart content was added
        self.assertEqual(self.file_hierarchy.content.smart_content, "Smart content for file")
        self.assertEqual(self.test_class.content.smart_content, "Smart content for class")
        self.assertEqual(self.method.content.smart_content, "Smart content for method")
        self.assertEqual(self.function.content.smart_content, "Smart content for function")

    @patch('asyncio.run')
    def test_process_skips_elements_with_up_to_date_smart_content(self, mock_asyncio_run):
        """Test that process() skips elements that already have up-to-date smart content."""
        # Set some elements to already have smart content
        self.file_hierarchy.content.smart_content = "Existing smart content"
        self.file_hierarchy.content.smart_content_hash = self.file_hierarchy.content.raw_content_hash
        
        self.test_class.content.smart_content = "Existing class content"
        self.test_class.content.smart_content_hash = self.test_class.content.raw_content_hash
        
        # Mock _process_element to track calls
        process_element_calls = []
        async def mock_process_element(element, element_type):
            process_element_calls.append((element, element_type))
            element.content.smart_content = f"Smart content for {element_type}"
            element.content.smart_content_hash = element.content.raw_content_hash
        
        def custom_asyncio_run(coro):
            # Run the async mock synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(mock_process_element(
                    coro.cr_frame.f_locals['element'],
                    coro.cr_frame.f_locals['element_type']
                ))
            finally:
                loop.close()
                
        with patch('asyncio.run', side_effect=custom_asyncio_run):
            # Process the repo
            result = self.service.process(self.repo)
        
        # Verify results
        self.assertEqual(result["processed"], 2)  # Only method and function
        self.assertEqual(result["skipped"], 2)  # File and class were skipped
        self.assertEqual(result["errors"], [])
        
        # Verify only method and function were processed
        self.assertEqual(len(process_element_calls), 2)
        processed_types = [call[1] for call in process_element_calls]
        self.assertIn("method", processed_types)
        self.assertIn("function", processed_types)

    @patch('asyncio.run')
    def test_process_handles_errors_gracefully(self, mock_asyncio_run):
        """Test that process() handles errors gracefully and continues processing."""
        # Mock _process_element to raise an error for the class
        async def mock_process_element(element, element_type):
            if element_type == "class":
                raise ValueError("Test error processing class")
            element.content.smart_content = f"Smart content for {element_type}"
            element.content.smart_content_hash = element.content.raw_content_hash
        
        def custom_asyncio_run(coro):
            # Run the async mock synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(mock_process_element(
                    coro.cr_frame.f_locals['element'],
                    coro.cr_frame.f_locals['element_type']
                ))
            finally:
                loop.close()
                
        with patch('asyncio.run', side_effect=custom_asyncio_run):
            # Process the repo
            result = self.service.process(self.repo)
        
        # Verify results
        self.assertEqual(result["processed"], 3)  # file, method, function (class failed)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Test error processing class", result["errors"][0])

    def test_process_with_no_content(self):
        """Test that process() handles elements without content."""
        # Create a file hierarchy with no content
        empty_file = FileHierarchy(
            file_path=Path("empty.py"),
            language="python",
            classes=[],
            functions=[],
            content=None,  # No content
            node_id="file:empty.py",
            line_count=0,
            last_processed=datetime.now(),
            filesystem_last_modified=datetime.now()
        )
        
        repo = Repo(
            file_hierarchies=[empty_file],
            metadata=RepoMetadata(name="test_repo"),
            last_loaded=datetime.now()
        )
        
        # Process the repo
        result = self.service.process(repo)
        
        # Verify results
        self.assertEqual(result["processed"], 0)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["total_elements"], 0)

    def test_process_updates_graph_structure_refs(self):
        """Test that process() updates graph structure_refs if they don't match."""
        # Modify graph to have different structure_ref
        different_file = FileHierarchy(
            file_path=Path("different.py"),
            language="python",
            classes=[],
            functions=[],
            content=self.file_content,
            node_id="file:test.py",
            line_count=5,
            last_processed=datetime.now(),
            filesystem_last_modified=datetime.now()
        )
        
        # Update graph node to point to different object
        self.graph.nodes["file:test.py"]["data"]["structure_ref"] = different_file
        
        # Mock _process_element
        async def mock_process_element(element, element_type):
            pass
            
        def custom_asyncio_run(coro):
            # Run the async mock synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(mock_process_element(
                    coro.cr_frame.f_locals['element'],
                    coro.cr_frame.f_locals['element_type']
                ))
            finally:
                loop.close()
                
        with patch('asyncio.run', side_effect=custom_asyncio_run):
            # Process the repo
            self.service.process(self.repo)
        
        # Verify graph was updated to point to our repo's object
        self.assertIs(
            self.graph.nodes["file:test.py"]["data"]["structure_ref"],
            self.file_hierarchy
        )

    def test_process_returns_correct_statistics(self):
        """Test that process() returns accurate statistics."""
        # Create a more complex repo
        file2 = FileHierarchy(
            file_path=Path("test2.py"),
            language="python",
            classes=[],
            functions=[
                Function(
                    name="func1",
                    node_id="function:test2.py:func1",
                    content=self.function_content,
                    parameters=[],
                    start_line=1,
                    end_line=2
                ),
                Function(
                    name="func2", 
                    node_id="function:test2.py:func2",
                    content=self.function_content,
                    parameters=[],
                    start_line=3,
                    end_line=4
                )
            ],
            content=self.file_content,
            node_id="file:test2.py",
            line_count=5,
            last_processed=datetime.now(),
            filesystem_last_modified=datetime.now()
        )
        
        repo = Repo(
            file_hierarchies=[self.file_hierarchy, file2],
            metadata=RepoMetadata(name="test_repo"),
            last_loaded=datetime.now()
        )
        
        # Mock _process_element
        async def mock_process_element(element, element_type):
            pass
            
        def custom_asyncio_run(coro):
            # Run the async mock synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(mock_process_element(
                    coro.cr_frame.f_locals['element'],
                    coro.cr_frame.f_locals['element_type']
                ))
            finally:
                loop.close()
                
        with patch('asyncio.run', side_effect=custom_asyncio_run):
            # Process the repo
            result = self.service.process(repo)
        
        # Verify statistics
        self.assertEqual(result["total_elements"], 7)  # 2 files, 1 class, 1 method, 3 functions
        

if __name__ == "__main__":
    unittest.main()