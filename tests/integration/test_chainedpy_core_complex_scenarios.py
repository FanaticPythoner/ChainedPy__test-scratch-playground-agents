"""
Complex scenario tests for ChainedPy.

Tests real-world complex scenarios with nested conditions, parallel operations,
mixed sync/async operations, and complex data flows. NO exception swallowing.
"""
from __future__ import annotations

# 1. Standard library imports
import asyncio
import json
import os
import sys
from collections import namedtuple
from dataclasses import dataclass, field
from typing import List, Dict, NamedTuple

# 2. Third-party imports
import pytest

# 3. Internal constants
# (none)

# 4. ChainedPy services
# (none)

# 5. ChainedPy internal modules
from chainedpy.chain import Chain
from chainedpy.plugins.processors import Proc

# 6. Test utilities
# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestComplexNestedConditions:
    """Test complex nested conditional scenarios."""
    
    @pytest.mark.asyncio
    async def test_deeply_nested_if_conditions(self):
        """Test deeply nested if conditions with multiple levels.

        :return None: None
        """
        # @@ STEP 1: Set up complex nested scenario - user permission system. @@
        user_data = {
            "role": "admin",
            "permissions": ["read", "write", "delete"],
            "active": True,
            "department": "engineering",
            "clearance_level": 5
        }
        
        result = await (
            Chain(user_data)
            .then_if(
                condition=lambda user: user["active"],
                then=lambda user: (
                    Chain(user)
                    .then_if(
                        condition=lambda u: u["role"] == "admin",
                        then=lambda u: (
                            Chain(u)
                            .then_if(
                                condition=lambda admin: "delete" in admin["permissions"],
                                then=lambda admin: (
                                    Chain(admin)
                                    .then_if(
                                        condition=lambda a: a["clearance_level"] >= 5,
                                        then=lambda a: { 
                                            **a,
                                            "access_level": "FULL_ACCESS",
                                            "can_delete": True,
                                            "can_modify_users": True
                                        },
                                        otherwise=lambda a: { 
                                            **a,
                                            "access_level": "LIMITED_ADMIN",
                                            "can_delete": True,
                                            "can_modify_users": False
                                        }
                                    )
                                ),
                                otherwise=lambda admin: { 
                                    **admin,
                                    "access_level": "READ_WRITE_ADMIN",
                                    "can_delete": False,
                                    "can_modify_users": False
                                }
                            )
                        ),
                        otherwise=lambda u: (
                            Chain(u)
                            .then_if( 
                                condition=lambda usr: usr["department"] == "engineering",
                                then=lambda usr_eng: {
                                    **usr_eng,
                                    "access_level": "ENGINEERING_ACCESS",
                                    "can_delete": False,
                                    "can_modify_users": False
                                },
                                otherwise=lambda usr_other: {
                                    **usr_other,
                                    "access_level": "BASIC_ACCESS",
                                    "can_delete": False,
                                    "can_modify_users": False
                                }
                            )
                        )
                    )
                ),
                otherwise=lambda user: { 
                    **user,
                    "access_level": "NO_ACCESS",
                    "can_delete": False,
                    "can_modify_users": False
                }
            )
        )
        
        assert result["access_level"] == "FULL_ACCESS"
        assert result["can_delete"] is True
        assert result["can_modify_users"] is True
    
    @pytest.mark.asyncio
    async def test_complex_elif_chains(self):
        """Test complex elif chains with multiple conditions.

        :raises AssertionError: If complex elif chain logic doesn't work as expected.
        :return None: None
        """
        # @@ STEP 1: Complex grading system with multiple criteria. @@
        student_data = {
            "exam_score": 85,
            "homework_avg": 90,
            "attendance": 0.95,
            "participation": 8,
            "extra_credit": 5
        }
        
        # Helper function to determine grade based on scores
        def determine_grade(s):
            if s["exam_score"] >= 95 and s["homework_avg"] >= 95 and s["attendance"] >= 0.95:
                return "A+"
            elif s["exam_score"] >= 90 and s["homework_avg"] >= 90 and s["attendance"] >= 0.90:
                return "A"
            elif s["exam_score"] >= 85 and s["homework_avg"] >= 85 and s["attendance"] >= 0.90:
                return "A-"
            elif s["exam_score"] >= 80 and s["homework_avg"] >= 80 and s["attendance"] >= 0.85:
                return "B+"
            else:
                return "B"

        # TODO (AUGMENT, IGNORE THIS): Ensure that ChainedPy is able to infer the type of the final variable / return value instead of "Any" even in the most complex cases.
        result = await (
            Chain(student_data)
            .then_map(lambda s: {**s, "calculated_grade": determine_grade(s)})
            .then_switch(
                key=lambda s: s["calculated_grade"],  # Extract the grade for switching
                cases={
                    "A+": lambda s: {**s, "grade": "A+", "gpa": 4.0}, 
                    "A": lambda s: {**s, "grade": "A", "gpa": 4.0},   
                    "A-": lambda s: {**s, "grade": "A-", "gpa": 3.7}, 
                    "B+": lambda s: {**s, "grade": "B+", "gpa": 3.3}, 
                },
                default=lambda s: {**s, "grade": "B", "gpa": 3.0} 
            )
            # Apply extra credit bonus
            .then_if(
                condition=lambda s: s.get("extra_credit", 0) > 0,
                then=lambda s: { 
                    **s,
                    "final_score": s["exam_score"] + min(s["extra_credit"], 10),
                    "has_extra_credit": True
                },
                otherwise=lambda s: { 
                    **s,
                    "final_score": s["exam_score"],
                    "has_extra_credit": False
                }
            )
        )
        
        assert result["grade"] == "A-"
        assert result["gpa"] == 3.7
        assert result["final_score"] == 90  # 85 + 5 extra credit
        assert result["has_extra_credit"] is True

    @pytest.mark.asyncio
    async def test_complex_switch_with_nested_conditions(self):
        """Test switch statements with nested conditional logic.

        :raises AssertionError: If complex switch with nested conditions doesn't work.
        :return None: None
        """
        # @@ STEP 1: Complex order processing system. @@
        order_data = {
            "type": "premium",
            "amount": 1500.00,
            "customer_tier": "gold",
            "region": "US",
            "items": [
                {"id": 1, "category": "electronics", "price": 800},
                {"id": 2, "category": "accessories", "price": 700}
            ]
        }

        result = await (
            Chain(order_data)
            .then_switch(
                key=lambda order: order["type"],  # Extract the type for switching
                cases={
                    "premium": lambda order: (
                        Chain(order)
                        .then_if(
                            condition=lambda o: o["amount"] > 1000,
                            # High value premium order
                            then=lambda o: (
                                Chain(o)
                                .then_if(
                                    condition=lambda ord_details: ord_details["customer_tier"] == "gold",
                                    # Gold customer premium order
                                    then=lambda ord_gold: {
                                        **ord_gold,
                                        "processing_priority": "URGENT",
                                        "discount": 0.15,
                                        "free_shipping": True,
                                        "expedited": True
                                    },
                                    # Regular customer premium order
                                    otherwise=lambda ord_regular: {
                                        **ord_regular,
                                        "processing_priority": "HIGH",
                                        "discount": 0.10,
                                        "free_shipping": True,
                                        "expedited": False
                                    }
                                )
                            ),
                            # Low value premium order
                            otherwise=lambda o: {
                                **o,
                                "processing_priority": "NORMAL",
                                "discount": 0.05,
                                "free_shipping": False,
                                "expedited": False
                            }
                        )
                    ),

                    "standard": lambda order: {
                        **order,
                        "processing_priority": "NORMAL",
                        "discount": 0.0,
                        "free_shipping": order["amount"] > 500,
                        "expedited": False
                    },

                    "economy": lambda order: {
                        **order,
                        "processing_priority": "LOW",
                        "discount": 0.0,
                        "free_shipping": False,
                        "expedited": False
                    }
                },
                # Default case for unknown order types
                default=lambda order: {
                    **order,
                    "processing_priority": "MANUAL_REVIEW",
                    "discount": 0.0,
                    "free_shipping": False,
                    "expedited": False
                }
            )
            # Apply regional adjustments
            .then_if(
                condition=lambda order: order["region"] in ["US", "CA"],
                then=lambda order: { 
                    **order,
                    "tax_rate": 0.08,
                    "currency": "USD"
                },
                otherwise=lambda order: { 
                    **order,
                    "tax_rate": 0.20,
                    "currency": "EUR"
                }
            )
        )

        assert result["processing_priority"] == "URGENT"
        assert result["discount"] == 0.15
        assert result["free_shipping"] is True
        assert result["expedited"] is True
        assert result["tax_rate"] == 0.08
        assert result["currency"] == "USD"


class TestComplexParallelOperations:
    """Test complex parallel operations with nested logic."""

    @pytest.mark.asyncio
    async def test_parallel_data_processing_with_conditions(self):
        """Test parallel processing with conditional logic in each branch.

        :raises AssertionError: If parallel data processing doesn't work as expected.
        :return None: None
        """
        # @@ STEP 1: Complex data processing scenario. @@
        raw_data = {
            "users": [
                {"id": 1, "name": "Alice", "age": 30, "department": "engineering"},
                {"id": 2, "name": "Bob", "age": 25, "department": "sales"},
                {"id": 3, "name": "Charlie", "age": 35, "department": "engineering"}
            ],
            "timestamp": "2024-01-15T10:30:00Z",
            "source": "api"
        }

        result = await (
            Chain(raw_data)
            .then_parallel(
                # Branch 1: Process users with age filtering and department grouping
                (
                    Chain(raw_data)
                    .then_map(lambda data: data["users"])
                    .then_foreach(
                        transform=lambda user: (
                            Chain(user)
                            .then_if(
                                condition=lambda u: u["age"] >= 30,
                                then=lambda u: {**u, "seniority": "senior"}, 
                                otherwise=lambda u: {**u, "seniority": "junior"} 
                            )
                        )
                    )
                    .then_map(lambda users: {
                        "engineering": [u for u in users if u["department"] == "engineering"],
                        "sales": [u for u in users if u["department"] == "sales"],
                        "other": [u for u in users if u["department"] not in ["engineering", "sales"]]
                    })
                ),

                # Branch 2: Process metadata with timestamp parsing
                (
                    Chain(raw_data)
                    .then_map(lambda data: {
                        "processed_at": data["timestamp"],
                        "source_system": data["source"],
                        "record_count": len(data["users"])
                    })
                    .then_if(
                        condition=lambda meta: meta["source_system"] == "api",
                        then=lambda meta: {
                            **meta,
                            "validation_required": True,
                            "priority": "high"
                        },
                        otherwise=lambda meta: {
                            **meta,
                            "validation_required": False,
                            "priority": "normal"
                        }
                    )
                ),

                # Branch 3: Generate statistics
                (
                    Chain(raw_data)
                    .then_map(lambda data: data["users"])
                    .then_map(lambda users: {
                        "total_users": len(users),
                        "avg_age": sum(u["age"] for u in users) / len(users) if users else 0,
                        "departments": list(set(u["department"] for u in users))
                    })
                )
            )
        )

        user_groups, metadata, stats = result

        # Verify user processing
        assert len(user_groups["engineering"]) == 2
        assert len(user_groups["sales"]) == 1
        assert user_groups["engineering"][0]["seniority"] == "senior"  # Alice, age 30
        assert user_groups["engineering"][1]["seniority"] == "senior"  # Charlie, age 35
        assert user_groups["sales"][0]["seniority"] == "junior"  # Bob, age 25

        # Verify metadata processing
        assert metadata["validation_required"] is True
        assert metadata["priority"] == "high"
        assert metadata["record_count"] == 3

        # Verify statistics
        assert stats["total_users"] == 3
        assert stats["avg_age"] == 30.0  # (30 + 25 + 35) / 3
        assert set(stats["departments"]) == {"engineering", "sales"}

    @pytest.mark.asyncio
    async def test_nested_parallel_with_foreach_and_conditions(self):
        """Test nested parallel operations with foreach and conditional logic.

        :raises AssertionError: If nested parallel operations don't work as expected.
        :return None: None
        """
        # @@ STEP 1: Complex batch processing scenario. @@
        batch_data = {
            "batches": [
                {
                    "id": "batch_1",
                    "items": [
                        {"type": "image", "size": 1024, "format": "jpg"},
                        {"type": "video", "size": 5120, "format": "mp4"},
                        {"type": "document", "size": 256, "format": "pdf"}
                    ]
                },
                {
                    "id": "batch_2",
                    "items": [
                        {"type": "image", "size": 2048, "format": "png"},
                        {"type": "audio", "size": 1536, "format": "mp3"}
                    ]
                }
            ]
        }

        result = await (
            Chain(batch_data)
            .then_map(lambda x: x['batches'])
            .then_parallel_foreach(
                transform=lambda batch_chain: (
                    Chain(batch_chain)
                    .then_map(lambda b_dict: b_dict["items"])
                    .then_parallel_foreach(
                        transform=lambda item_chain: (
                            Chain(item_chain)
                            .then_if(
                                condition=lambda i_dict: i_dict["type"] == "image",
                                # Image processing
                                then=lambda i_chain: (
                                    Chain(i_chain)
                                    .then_if(
                                        condition=lambda img_dict: img_dict["size"] > 1500,
                                        then=lambda img_dict_large: { 
                                            **img_dict_large,
                                            "processing": "compress",
                                            "target_size": img_dict_large["size"] // 2,
                                            "priority": "high"
                                        },
                                        otherwise=lambda img_dict_small: { 
                                            **img_dict_small,
                                            "processing": "optimize",
                                            "target_size": img_dict_small["size"],
                                            "priority": "normal"
                                        }
                                    )
                                ),
                                otherwise=lambda i_chain: (
                                    Chain(i_chain)
                                    .then_switch(
                                        key=lambda i_dict_other: i_dict_other["type"],
                                        cases={
                                            "video": lambda vid_dict: {
                                                **vid_dict,
                                                "processing": "transcode",
                                                "target_format": "h264",
                                                "priority": "high"
                                            }, 
                                            "audio": lambda aud_dict: {
                                                **aud_dict,
                                                "processing": "normalize",
                                                "target_bitrate": "320k",
                                                "priority": "normal"
                                            }, 
                                            "document": lambda doc_dict: {
                                                **doc_dict,
                                                "processing": "ocr",
                                                "target_format": "searchable_pdf",
                                                "priority": "low"
                                            } 
                                        },
                                        default=lambda unknown_dict: unknown_dict 
                                    )
                                )
                            )
                        )
                    )
                    .then_map(lambda processed_items_list: {
                        "batch_id": batch_chain["id"], 
                        "items": processed_items_list,
                        "total_items": len(processed_items_list),
                        "high_priority_count": len([i for i in processed_items_list if i["priority"] == "high"])
                    })
                )
            )
        )

        # Verify batch 1 processing
        batch1 = next(b for b in result if b["batch_id"] == "batch_1")
        assert batch1["total_items"] == 3
        assert batch1["high_priority_count"] == 1  # Only video is high priority

        # Find specific items
        image_item = next(i for i in batch1["items"] if i["type"] == "image")
        video_item = next(i for i in batch1["items"] if i["type"] == "video")
        doc_item = next(i for i in batch1["items"] if i["type"] == "document")

        assert image_item["processing"] == "optimize"  # size 1024 <= 1500
        assert image_item["priority"] == "normal"
        assert video_item["processing"] == "transcode"
        assert video_item["priority"] == "high"
        assert doc_item["processing"] == "ocr"
        assert doc_item["priority"] == "low"

        # Verify batch 2 processing
        batch2 = next(b for b in result if b["batch_id"] == "batch_2")
        assert batch2["total_items"] == 2
        assert batch2["high_priority_count"] == 1  # Image with size 2048 > 1500 is high priority

        image2_item = next(i for i in batch2["items"] if i["type"] == "image")
        audio_item = next(i for i in batch2["items"] if i["type"] == "audio")

        assert image2_item["processing"] == "compress"  # size 2048 > 1500
        assert image2_item["priority"] == "high"
        assert audio_item["processing"] == "normalize"
        assert audio_item["priority"] == "normal"


class TestComplexMixedAsyncSync:
    """Test complex scenarios mixing async and sync operations."""

    @pytest.mark.asyncio
    async def test_complex_async_sync_pipeline_with_conditions(self):
        """Test complex pipeline mixing async/sync with conditional logic.

        :raises AssertionError: If async/sync pipeline doesn't work as expected.
        :return None: None
        """
        # Simulate complex data processing pipeline
        input_data = {
            "requests": [
                {"id": 1, "type": "api_call", "url": "https://api.example.com/users", "timeout": 5},
                {"id": 2, "type": "database", "query": "SELECT * FROM products", "timeout": 10},
                {"id": 3, "type": "file_read", "path": "/data/config.json", "timeout": 2}
            ]
        }

        # Async simulation functions
        async def simulate_api_call(request):
            await asyncio.sleep(0.01)  # Simulate network delay
            return {
                "id": request["id"],
                "status": "success",
                "data": [{"user_id": i, "name": f"User{i}"} for i in range(1, 4)],
                "response_time": 0.05
            }

        async def simulate_db_query(request):
            await asyncio.sleep(0.02)  # Simulate DB delay
            return {
                "id": request["id"],
                "status": "success",
                "data": [{"product_id": i, "name": f"Product{i}"} for i in range(1, 6)],
                "response_time": 0.1
            }

        def simulate_file_read(request):
            # Sync operation
            return {
                "id": request["id"],
                "status": "success",
                "data": {"config_version": "1.2.3", "debug": True},
                "response_time": 0.001
            }

        result = await (
            Chain(input_data)
            .then_map(lambda data: data["requests"])
            .then_parallel_foreach(
                transform=lambda request_chain: (
                    Chain(request_chain)
                    .then_if(
                        condition=lambda req_dict: req_dict["type"] == "api_call",
                        # API call branch (async)
                        then=lambda api_req_chain: (
                            Chain(api_req_chain)
                            .then_map(simulate_api_call)
                            .then_if(
                                condition=lambda response: response["status"] == "success",
                                then=lambda response: {
                                    **response,
                                    "processed": True,
                                    "data_count": len(response["data"]),
                                    "performance": "good" if response["response_time"] < 0.1 else "slow"
                                },
                                otherwise=lambda response: {
                                    **response,
                                    "processed": False,
                                    "error": "API call failed"
                                }
                            )
                        ),
                        otherwise=lambda other_req_chain: (
                            Chain(other_req_chain)
                            .then_switch(
                                key=lambda req_dict_inner: req_dict_inner["type"],
                                cases={
                                    "database": lambda db_req_chain: (
                                        Chain(db_req_chain)
                                        .then_map(simulate_db_query)
                                        .then_if(
                                            condition=lambda response: response["status"] == "success",
                                            then=lambda response: {
                                                **response,
                                                "processed": True,
                                                "data_count": len(response["data"]),
                                                "performance": "good" if response["response_time"] < 0.2 else "slow"
                                            },
                                            otherwise=lambda response: {
                                                **response,
                                                "processed": False,
                                                "error": "Database query failed"
                                            }
                                        )
                                    ),
                                    "file_read": lambda file_req_chain: (
                                        Chain(file_req_chain)
                                        .then_map(simulate_file_read)
                                        .then_if(
                                            condition=lambda response: response["status"] == "success",
                                            then=lambda response: {
                                                **response,
                                                "processed": True,
                                                "data_type": type(response["data"]).__name__,
                                                "performance": "excellent"
                                            },
                                            otherwise=lambda response: {
                                                **response,
                                                "processed": False,
                                                "error": "File read failed"
                                            }
                                        )
                                    )
                                },
                                default=lambda unknown_req_dict: unknown_req_dict 
                            )
                        )
                    )
                )
            )
            # Post-process results
            .then_map(lambda responses: {
                "total_requests": len(responses),
                "successful": [r for r in responses if r["processed"]],
                "failed": [r for r in responses if not r["processed"]],
                "performance_summary": {
                    "excellent": len([r for r in responses if r.get("performance") == "excellent"]),
                    "good": len([r for r in responses if r.get("performance") == "good"]),
                    "slow": len([r for r in responses if r.get("performance") == "slow"])
                }
            })
        )

        assert result["total_requests"] == 3
        assert len(result["successful"]) == 3
        assert len(result["failed"]) == 0

        # Verify API call result
        api_result = next(r for r in result["successful"] if r["id"] == 1)
        assert api_result["data_count"] == 3
        assert api_result["performance"] == "good"

        # Verify database result
        db_result = next(r for r in result["successful"] if r["id"] == 2)
        assert db_result["data_count"] == 5
        assert db_result["performance"] == "good"

        # Verify file read result
        file_result = next(r for r in result["successful"] if r["id"] == 3)
        assert file_result["data_type"] == "dict"
        assert file_result["performance"] == "excellent"

        # Verify performance summary
        assert result["performance_summary"]["excellent"] == 1
        assert result["performance_summary"]["good"] == 2
        assert result["performance_summary"]["slow"] == 0


class TestComplexErrorHandlingScenarios:
    """Test complex error handling with nested operations and recovery."""

    @pytest.mark.asyncio
    async def test_complex_error_recovery_with_nested_conditions(self):
        """Test complex error recovery scenarios with nested conditional logic.

        :raises AssertionError: If error recovery doesn't work as expected.
        :return None: None
        """
        # Simulate a complex data processing pipeline with potential failures
        problematic_data = [
            {"id": 1, "data": "123", "type": "number", "backup": "456"},
            {"id": 2, "data": "invalid", "type": "number", "backup": "789"},
            {"id": 3, "data": '{"key": "value"}', "type": "json", "backup": '{"fallback": true}'},
            {"id": 4, "data": '{"invalid": json}', "type": "json", "backup": '{"fallback": true}'},
            {"id": 5, "data": "aGVsbG8=", "type": "base64", "backup": "d29ybGQ="}
        ]

        # Helper function to safely process numbers
        def safe_process_number(item_dict):
            try:
                result = int(item_dict["data"])
                return {"id": item_dict["id"], "result": result, "status": "success", "used_backup": False}
            except ValueError:
                result = int(item_dict["backup"])
                return {"id": item_dict["id"], "result": result, "status": "recovered", "used_backup": True}

        # Helper function to safely process JSON
        def safe_process_json(item_dict):
            try:
                result = json.loads(item_dict["data"])
                return {"id": item_dict["id"], "result": result, "status": "success", "used_backup": False}
            except json.JSONDecodeError:
                result = json.loads(item_dict["backup"])
                return {"id": item_dict["id"], "result": result, "status": "recovered", "used_backup": True}

        result = await (
            Chain(problematic_data)
            .then_foreach(
                transform=lambda item_chain: (
                    Chain(item_chain)
                    .then_if(
                        condition=lambda i_dict: i_dict["type"] == "number",
                        then=lambda i_chain_num: safe_process_number(i_chain_num),
                        otherwise=lambda i_chain_other: (
                            Chain(i_chain_other)
                            .then_switch(
                                key=lambda i_dict_sw: i_dict_sw["type"],
                                cases={
                                    "json": lambda json_item_chain: safe_process_json(json_item_chain),
                                    "base64": lambda b64_item_chain: (
                                        Chain(b64_item_chain)
                                        .then_map(lambda b64_dict: b64_dict["data"])
                                        .then_process(Proc.B64_DECODE)
                                        .then_map(lambda decoded_bytes: {
                                            "id": b64_item_chain["id"],
                                            "result": decoded_bytes.decode(), 
                                            "status": "success", 
                                            "used_backup": False
                                        })
                                    )
                                },
                                default=lambda unknown_item_dict: unknown_item_dict
                            )
                        )
                    )
                )
            )
            .then_map(lambda results: {
                "total_processed": len(results),
                "successful": [r for r in results if r["status"] == "success"],
                "recovered": [r for r in results if r["status"] == "recovered"],
                "failed": [r for r in results if r["status"] == "failed"],
                "backup_usage_rate": len([r for r in results if r["used_backup"]]) / len(results)
            })
        )

        assert result["total_processed"] == 5
        assert len(result["successful"]) == 3  # Items 1, 3, 5 succeed on first try
        assert len(result["recovered"]) == 2   # Items 2, 4 use backup data
        assert len(result["failed"]) == 0      # No complete failures
        assert result["backup_usage_rate"] == 0.4  # 2/5 = 40%

        # Verify specific recoveries
        recovered_items = {r["id"]: r for r in result["recovered"]}
        assert recovered_items[2]["result"] == 789  # Backup number for invalid "invalid"
        assert recovered_items[4]["result"] == {"fallback": True}  # Backup JSON

    @pytest.mark.asyncio
    async def test_complex_retry_with_conditional_logic(self):
        """Test complex retry scenarios with conditional retry strategies.

        :raises AssertionError: If retry logic doesn't work as expected.
        :return None: None
        """
        # Simulate unreliable service calls with different retry strategies
        call_attempts = {"api_1": 0, "api_2": 0, "api_3": 0}

        async def unreliable_api_call(service_name: str, data: dict):
            call_attempts[service_name] += 1

            if service_name == "api_1":
                # Fails first 2 times, succeeds on 3rd
                if call_attempts[service_name] < 3:
                    raise ConnectionError(f"API {service_name} connection failed")
                return {"service": service_name, "data": data, "attempt": call_attempts[service_name]}

            elif service_name == "api_2":
                # Always fails with timeout
                raise TimeoutError(f"API {service_name} timeout")

            else:  # api_3
                # Succeeds immediately
                return {"service": service_name, "data": data, "attempt": call_attempts[service_name]}

        services_data = [
            {"name": "api_1", "data": {"user_id": 123}, "critical": True},
            {"name": "api_2", "data": {"order_id": 456}, "critical": False},
            {"name": "api_3", "data": {"product_id": 789}, "critical": True}
        ]

        result = await (
            Chain(services_data)
            .then_parallel_foreach(
                transform=lambda service_chain: (
                    Chain(service_chain)
                    .then_if(
                        condition=lambda s_dict: s_dict["critical"],
                        then=lambda crit_service_chain: (
                            Chain(crit_service_chain)
                            .then_map(lambda svc_dict_crit: unreliable_api_call(svc_dict_crit["name"], svc_dict_crit["data"]))
                            .as_retry(attempts=5, delay=0.01)
                            .as_on_error(
                                lambda error: {
                                    "service": crit_service_chain["name"],
                                    "status": "failed",
                                    "error": str(error),
                                    "critical": True
                                }
                            )
                        ),
                        otherwise=lambda noncrit_service_chain: (
                            Chain(noncrit_service_chain)
                            .then_map(lambda svc_dict_noncrit: unreliable_api_call(svc_dict_noncrit["name"], svc_dict_noncrit["data"]))
                            .as_retry(attempts=2, delay=0.01)
                            .as_on_error(
                                lambda error: {
                                    "service": noncrit_service_chain["name"],
                                    "status": "failed",
                                    "error": str(error),
                                    "critical": False
                                }
                            )
                        )
                    )
                )
            )
            .then_map(lambda responses: {
                "total_services": len(responses),
                "successful": [r for r in responses if r.get("status") != "failed"],
                "failed": [r for r in responses if r.get("status") == "failed"],
                "critical_failures": [r for r in responses if r.get("status") == "failed" and r.get("critical")],
                "retry_summary": {
                    "api_1_attempts": call_attempts["api_1"],
                    "api_2_attempts": call_attempts["api_2"],
                    "api_3_attempts": call_attempts["api_3"]
                }
            })
        )

        assert result["total_services"] == 3
        assert len(result["successful"]) == 2  # api_1 and api_3 succeed
        assert len(result["failed"]) == 1      # api_2 fails
        assert len(result["critical_failures"]) == 0  # No critical service failures

        # Verify retry behavior
        assert result["retry_summary"]["api_1_attempts"] == 3  # Succeeded on 3rd attempt
        assert result["retry_summary"]["api_2_attempts"] == 2  # Failed after 2 attempts (non-critical)
        assert result["retry_summary"]["api_3_attempts"] == 1  # Succeeded immediately

        # Verify successful responses
        successful_services = {r["service"]: r for r in result["successful"]}
        assert successful_services["api_1"]["attempt"] == 3
        assert successful_services["api_3"]["attempt"] == 1

        # Verify failed response
        failed_service = result["failed"][0]
        assert failed_service["service"] == "api_2"
        assert "timeout" in failed_service["error"].lower()
        assert failed_service["critical"] is False


class TestComplexProcessorCombinations:
    """Test complex combinations of processors with conditional logic."""

    @pytest.mark.asyncio
    async def test_complex_data_transformation_pipeline(self):
        """Test complex data transformation using multiple processors and conditions.

        :raises AssertionError: If data transformation pipeline doesn't work as expected.
        :return None: None
        """
        # Complex data transformation scenario
        raw_input = {
            "config": '{"database": {"host": "localhost", "port": "5432"}, "cache": {"ttl": "3600"}}',
            "encoded_secrets": "eyJ1c2VyIjogImFkbWluIiwgInBhc3MiOiAic2VjcmV0MTIzIn0=",  # {"user": "admin", "pass": "secret123"}
            "user_input": "  JOHN DOE  ",
            "numeric_data": ["123", "456.78", "999"],
            "flags": "true,false,true,false"
        }

        result = await (
            Chain(raw_input)
            .then_parallel(
                # Branch 1: Process configuration
                (
                    Chain(raw_input)
                    .then_map(lambda data: data["config"])
                    .then_process(Proc.JSON_LOADS)
                    .then_if(
                        condition=lambda config: "database" in config,
                        then=lambda config: {
                            **config,
                            "database": {
                                **config["database"],
                                "port": int(config["database"]["port"])  # Convert port to int
                            }
                        },
                        otherwise=lambda config: config  # No change if no database config
                    )
                    .then_if(
                        condition=lambda config: "cache" in config,
                        then=lambda config: {
                            **config,
                            "cache": {
                                **config["cache"],
                                "ttl": int(config["cache"]["ttl"])  # Convert TTL to int
                            }
                        },
                        otherwise=lambda config: config  # No change if no cache config
                    )
                ),

                # Branch 2: Process secrets
                (
                    Chain(raw_input)
                    .then_map(lambda data: data["encoded_secrets"])
                    .then_process(Proc.B64_DECODE)
                    .then_map(lambda decoded: decoded.decode())
                    .then_process(Proc.JSON_LOADS)
                    .then_if(
                        condition=lambda secrets: "user" in secrets and "pass" in secrets,
                        then=lambda secrets: {
                            "username": secrets["user"].upper(),
                            "password_length": len(secrets["pass"]),
                            "has_credentials": True
                        },
                        otherwise=lambda _: {"has_credentials": False}  # Fixed unused parameter
                    )
                ),

                # Branch 3: Process user input
                (
                    Chain(raw_input)
                    .then_map(lambda data: data["user_input"])
                    .then_process(Proc.STRIP)
                    .then_process(Proc.LOWER)
                    .then_map(lambda name: {
                        "formatted_name": name.title(),
                        "name_parts": name.split(),
                        "character_count": len(name.replace(" ", ""))
                    })
                ),

                # Branch 4: Process numeric data
                (
                    Chain(raw_input)
                    .then_map(lambda data: data["numeric_data"])
                    .then_foreach( # then_foreach provides Chain(element) to transform
                        transform=lambda num_str_chain: ( # num_str_chain is Chain(string_number)
                            Chain(num_str_chain)
                            .then_if(
                                condition=lambda s_val: "." in s_val, # s_val is the string number
                                then=lambda s_chain_float: (
                                    Chain(s_chain_float)
                                    .then_process(Proc.TO_FLOAT)
                                ), 
                                otherwise=lambda s_chain_int: (
                                    Chain(s_chain_int)
                                    .then_process(Proc.TO_INT)
                                )
                            )
                        )
                    )
                    .then_map(lambda numbers: {
                        "total": sum(numbers),
                        "count": len(numbers),
                        "average": sum(numbers) / len(numbers) if numbers else 0,
                        "integers": [n for n in numbers if isinstance(n, int)],
                        "floats": [n for n in numbers if isinstance(n, float)]
                    })
                ),

                # Branch 5: Process flags
                (
                    Chain(raw_input)
                    .then_map(lambda data: data["flags"])
                    .then_map(lambda flags_str: flags_str.split(",")) # Now a list of flag strings
                    .then_foreach( # then_foreach provides Chain(flag_string)
                        transform=lambda flag_str_chain: ( # flag_str_chain is Chain(flag_string)
                            Chain(flag_str_chain)
                            .then_if(
                                condition=lambda f_str: f_str.lower() == "true",
                                then=lambda _: True, 
                                otherwise=lambda _: False
                            )
                        )
                    )
                    .then_map(lambda flags: {
                        "flags": flags,
                        "true_count": sum(flags),
                        "false_count": len(flags) - sum(flags),
                        "all_true": all(flags) if flags else False, # Handle empty flags list
                        "any_true": any(flags)
                    })
                )
            )
        )

        config, secrets, user_data, numeric_data, flags_data = result

        # Verify configuration processing
        assert config["database"]["host"] == "localhost"
        assert config["database"]["port"] == 5432  # Converted to int
        assert config["cache"]["ttl"] == 3600      # Converted to int

        # Verify secrets processing
        assert secrets["username"] == "ADMIN"
        assert secrets["password_length"] == 9
        assert secrets["has_credentials"] is True

        # Verify user input processing
        assert user_data["formatted_name"] == "John Doe"
        assert user_data["name_parts"] == ["john", "doe"]
        assert user_data["character_count"] == 7  # "johndoe" without space

        # Verify numeric data processing
        assert numeric_data["total"] == 123 + 456.78 + 999  # 1578.78
        assert numeric_data["count"] == 3
        assert abs(numeric_data["average"] - 526.26) < 0.01
        assert numeric_data["integers"] == [123, 999]
        assert numeric_data["floats"] == [456.78]

        # Verify flags processing
        assert flags_data["flags"] == [True, False, True, False]
        assert flags_data["true_count"] == 2
        assert flags_data["false_count"] == 2
        assert flags_data["all_true"] is False
        assert flags_data["any_true"] is True


class TestComplexClassInstanceScenarios:
    """Test complex scenarios with class instances passed to Chain() constructor."""

    @pytest.mark.asyncio
    async def test_custom_class_instances_with_methods(self):
        """Test Chain() with custom class instances that have methods and properties.

        :raises AssertionError: If custom class instance operations don't work as expected.
        :return None: None
        """

        class User:
            def __init__(self, name: str, age: int, email: str):
                self.name = name
                self.age = age
                self.email = email
                self._permissions = set()
                self._login_count = 0

            def add_permission(self, permission: str):
                self._permissions.add(permission)
                return self

            def get_permissions(self):
                return list(self._permissions)

            def increment_login(self):
                self._login_count += 1
                return self._login_count

            def is_adult(self):
                return self.age >= 18

            def get_domain(self):
                return self.email.split('@')[1] if '@' in self.email else None

            def __str__(self):
                return f"User({self.name}, {self.age})"

            def __repr__(self):
                return f"User(name='{self.name}', age={self.age}, email='{self.email}')"

        # Create user instance
        user = User("Alice Johnson", 28, "alice@company.com")
        user.add_permission("read").add_permission("write")

        result = await (
            Chain(user)
            .then_if(
                condition=lambda u: u.is_adult(),
                then=lambda u: (
                    Chain(u)
                    .then_map(lambda user_obj: {
                        "name": user_obj.name,
                        "age": user_obj.age,
                        "email": user_obj.email,
                        "domain": user_obj.get_domain(),
                        "permissions": user_obj.get_permissions(),
                        "login_count": user_obj.increment_login(),
                        "is_adult": user_obj.is_adult(),
                        "str_repr": str(user_obj),
                        "repr": repr(user_obj)
                    })
                ),
                otherwise=lambda u: {
                    "name": u.name,
                    "age": u.age,
                    "access_denied": True
                }
            )
        )

        assert result["name"] == "Alice Johnson"
        assert result["age"] == 28
        assert result["email"] == "alice@company.com"
        assert result["domain"] == "company.com"
        assert set(result["permissions"]) == {"read", "write"}
        assert result["login_count"] == 1
        assert result["is_adult"] is True
        assert result["str_repr"] == "User(Alice Johnson, 28)"
        assert "User(name='Alice Johnson'" in result["repr"]

    @pytest.mark.asyncio
    async def test_dataclass_instances_with_complex_operations(self):
        """Test Chain() with dataclass instances and complex operations.

        :raises AssertionError: If dataclass instance operations don't work as expected.
        :return None: None
        """
        @dataclass
        class Product:
            id: int
            name: str
            price: float
            category: str
            tags: List[str] = field(default_factory=list)
            metadata: Dict[str, str] = field(default_factory=dict)

            def add_tag(self, tag: str):
                if tag not in self.tags:
                    self.tags.append(tag)
                return self

            def set_metadata(self, key: str, value: str):
                self.metadata[key] = value
                return self

            def get_discounted_price(self, discount: float):
                return self.price * (1 - discount)

            def is_expensive(self, threshold: float = 100.0):
                return self.price > threshold

        # Create product instance
        product = Product(
            id=1001,
            name="Premium Laptop",
            price=1299.99,
            category="electronics"
        )
        product.add_tag("premium").add_tag("portable")
        product.set_metadata("warranty", "2 years").set_metadata("brand", "TechCorp")

        result = await (
            Chain(product)
            .then_if(
                condition=lambda p: p.is_expensive(1000.0),
                then=lambda p: (
                    Chain(p)
                    .then_map(lambda prod: {
                        "id": prod.id,
                        "name": prod.name,
                        "original_price": prod.price,
                        "discounted_price": prod.get_discounted_price(0.15),
                        "category": prod.category,
                        "tags": prod.tags,
                        "metadata": prod.metadata,
                        "is_premium": True,
                        "discount_applied": 0.15
                    })
                ),
                otherwise=lambda p: {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "is_premium": False
                }
            )
            .then_if(
                condition=lambda data: "electronics" in data.get("category", ""),
                then=lambda data: {
                    **data,
                    "shipping_cost": 0.0,  # Free shipping for electronics
                    "estimated_delivery": "2-3 days"
                },
                otherwise=lambda data: {
                    **data,
                    "shipping_cost": 9.99,
                    "estimated_delivery": "5-7 days"
                }
            )
        )

        assert result["id"] == 1001
        assert result["name"] == "Premium Laptop"
        assert result["original_price"] == 1299.99
        assert abs(result["discounted_price"] - 1104.99) < 0.01  # 15% discount
        assert result["category"] == "electronics"
        assert set(result["tags"]) == {"premium", "portable"}
        assert result["metadata"]["warranty"] == "2 years"
        assert result["metadata"]["brand"] == "TechCorp"
        assert result["is_premium"] is True
        assert result["shipping_cost"] == 0.0
        assert result["estimated_delivery"] == "2-3 days"

    @pytest.mark.asyncio
    async def test_named_tuple_instances_with_transformations(self):
        """Test Chain() with named tuple instances and complex transformations.

        :raises AssertionError: If named tuple instance operations don't work as expected.
        :return None: None
        """
        # Classic named tuple
        Point = namedtuple('Point', ['x', 'y', 'z'])

        # Modern typed named tuple
        class Vector(NamedTuple):
            x: float
            y: float
            z: float

            def magnitude(self):
                return (self.x**2 + self.y**2 + self.z**2)**0.5

            def normalize(self):
                mag = self.magnitude()
                if mag == 0:
                    return Vector(0, 0, 0)
                return Vector(self.x/mag, self.y/mag, self.z/mag)

            def dot_product(self, other):
                return self.x * other.x + self.y * other.y + self.z * other.z

        # Create instances
        point = Point(3, 4, 5)
        vector = Vector(1.0, 2.0, 2.0)

        result = await (
            Chain([point, vector])
            .then_parallel_foreach(
                transform=lambda item_chain: (
                    Chain(item_chain)
                    .then_if(
                        condition=lambda item: hasattr(item, 'magnitude'),
                        # Handle Vector (has methods)
                        then=lambda vec_chain: (
                            Chain(vec_chain)
                            .then_map(lambda v: {
                                "type": "vector",
                                "x": v.x,
                                "y": v.y,
                                "z": v.z,
                                "magnitude": v.magnitude(),
                                "normalized": v.normalize()._asdict(),
                                "is_unit_vector": abs(v.magnitude() - 1.0) < 0.001
                            })
                        ),
                        # Handle Point (basic named tuple)
                        otherwise=lambda point_chain: (
                            Chain(point_chain)
                            .then_map(lambda p: {
                                "type": "point",
                                "x": p.x,
                                "y": p.y,
                                "z": p.z,
                                "distance_from_origin": (p.x**2 + p.y**2 + p.z**2)**0.5,
                                "as_dict": p._asdict()
                            })
                        )
                    )
                )
            )
        )

        # Verify point result
        point_result = next(r for r in result if r["type"] == "point")
        assert point_result["x"] == 3
        assert point_result["y"] == 4
        assert point_result["z"] == 5
        assert abs(point_result["distance_from_origin"] - 7.071) < 0.01
        assert point_result["as_dict"] == {"x": 3, "y": 4, "z": 5}

        # Verify vector result
        vector_result = next(r for r in result if r["type"] == "vector")
        assert vector_result["x"] == 1.0
        assert vector_result["y"] == 2.0
        assert vector_result["z"] == 2.0
        assert abs(vector_result["magnitude"] - 3.0) < 0.001
        assert vector_result["is_unit_vector"] is False

        # Verify normalized vector
        normalized = vector_result["normalized"]
        assert abs(normalized["x"] - 1/3) < 0.001
        assert abs(normalized["y"] - 2/3) < 0.001
        assert abs(normalized["z"] - 2/3) < 0.001

    @pytest.mark.asyncio
    async def test_inheritance_hierarchy_with_polymorphism(self):
        """Test Chain() with inheritance hierarchies and polymorphic behavior.

        :raises AssertionError: If inheritance hierarchy operations don't work as expected.
        :return None: None
        """

        class Animal:
            def __init__(self, name: str, age: int):
                self.name = name
                self.age = age
                self._health = 100

            def make_sound(self):
                return "Generic animal sound"

            def get_info(self):
                return {
                    "name": self.name,
                    "age": self.age,
                    "type": self.__class__.__name__,
                    "health": self._health
                }

            def heal(self, amount: int):
                self._health = min(100, self._health + amount)
                return self

        class Dog(Animal):
            def __init__(self, name: str, age: int, breed: str):
                super().__init__(name, age)
                self.breed = breed
                self._tricks = []

            def make_sound(self):
                return "Woof!"

            def learn_trick(self, trick: str):
                if trick not in self._tricks:
                    self._tricks.append(trick)
                return self

            def get_tricks(self):
                return self._tricks.copy()

            def get_info(self):
                info = super().get_info()
                info.update({
                    "breed": self.breed,
                    "tricks": self.get_tricks(),
                    "sound": self.make_sound()
                })
                return info

        class Cat(Animal):
            def __init__(self, name: str, age: int, indoor: bool = True):
                super().__init__(name, age)
                self.indoor = indoor
                self._lives = 9

            def make_sound(self):
                return "Meow!"

            def use_life(self):
                if self._lives > 0:
                    self._lives -= 1
                return self._lives

            def get_info(self):
                info = super().get_info()
                info.update({
                    "indoor": self.indoor,
                    "lives_remaining": self._lives,
                    "sound": self.make_sound()
                })
                return info

        # Create animal instances
        dog = Dog("Buddy", 5, "Golden Retriever")
        dog.learn_trick("sit").learn_trick("fetch")

        cat = Cat("Whiskers", 3, indoor=True)
        cat.use_life()  # Now has 8 lives

        animals: list[Dog | Cat] = [dog, cat]

        result = await (
            Chain(animals)
            .then_foreach(
                transform=lambda animal_chain: (
                    Chain(animal_chain)
                    .then_map(lambda animal: animal.get_info())
                    .then_if(
                        condition=lambda info: info["type"] == "Dog",
                        then=lambda dog_info: {
                            **dog_info,
                            "category": "canine",
                            "can_fetch": "fetch" in dog_info.get("tricks", []),
                            "training_level": len(dog_info.get("tricks", []))
                        },
                        otherwise=lambda other_info: (
                            Chain(other_info)
                            .then_if(
                                condition=lambda info: info["type"] == "Cat",
                                then=lambda cat_info: {
                                    **cat_info,
                                    "category": "feline",
                                    "is_safe": cat_info.get("lives_remaining", 0) > 5,
                                    "lifestyle": "indoor" if cat_info.get("indoor") else "outdoor"
                                },
                                otherwise=lambda generic_info: {
                                    **generic_info,
                                    "category": "unknown"
                                }
                            )
                        )
                    )
                )
            )
        )

        # Verify dog result
        dog_result = next(r for r in result if r["type"] == "Dog")
        assert dog_result["name"] == "Buddy"
        assert dog_result["age"] == 5
        assert dog_result["breed"] == "Golden Retriever"
        assert dog_result["sound"] == "Woof!"
        assert dog_result["category"] == "canine"
        assert dog_result["can_fetch"] is True
        assert dog_result["training_level"] == 2
        assert set(dog_result["tricks"]) == {"sit", "fetch"}

        # Verify cat result
        cat_result = next(r for r in result if r["type"] == "Cat")
        assert cat_result["name"] == "Whiskers"
        assert cat_result["age"] == 3
        assert cat_result["sound"] == "Meow!"
        assert cat_result["category"] == "feline"
        assert cat_result["lives_remaining"] == 8
        assert cat_result["is_safe"] is True
        assert cat_result["lifestyle"] == "indoor"

    @pytest.mark.asyncio
    async def test_complex_object_state_management(self):
        """Test Chain() with objects that have complex internal state management.

        :raises AssertionError: If complex object state management doesn't work as expected.
        :return None: None
        """

        class BankAccount:
            def __init__(self, account_number: str, initial_balance: float = 0.0):
                self.account_number = account_number
                self._balance = initial_balance
                self._transaction_history = []
                self._is_frozen = False
                self._overdraft_limit = 0.0

            def deposit(self, amount: float, description: str = "Deposit"):
                if self._is_frozen:
                    raise ValueError("Account is frozen")
                if amount <= 0:
                    raise ValueError("Amount must be positive")

                self._balance += amount
                self._transaction_history.append({
                    "type": "deposit",
                    "amount": amount,
                    "description": description,
                    "balance_after": self._balance
                })
                return self

            def withdraw(self, amount: float, description: str = "Withdrawal"):
                if self._is_frozen:
                    raise ValueError("Account is frozen")
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                if self._balance - amount < -self._overdraft_limit:
                    raise ValueError("Insufficient funds")

                self._balance -= amount
                self._transaction_history.append({
                    "type": "withdrawal",
                    "amount": amount,
                    "description": description,
                    "balance_after": self._balance
                })
                return self

            def set_overdraft_limit(self, limit: float):
                self._overdraft_limit = max(0, limit)
                return self

            def freeze_account(self):
                self._is_frozen = True
                return self

            def unfreeze_account(self):
                self._is_frozen = False
                return self

            def get_balance(self):
                return self._balance

            def get_transaction_count(self):
                return len(self._transaction_history)

            def get_last_transaction(self):
                return self._transaction_history[-1] if self._transaction_history else None

            def get_account_summary(self):
                return {
                    "account_number": self.account_number,
                    "balance": self._balance,
                    "is_frozen": self._is_frozen,
                    "overdraft_limit": self._overdraft_limit,
                    "transaction_count": len(self._transaction_history),
                    "last_transaction": self.get_last_transaction()
                }

        # Create account and perform operations
        account = BankAccount("ACC-12345", 1000.0)
        account.set_overdraft_limit(500.0)
        account.deposit(250.0, "Salary").withdraw(100.0, "Groceries")

        result = await (
            Chain(account)
            .then_if(
                condition=lambda acc: acc.get_balance() > 500,
                then=lambda acc_chain: (
                    Chain(acc_chain)
                    .then_map(lambda acc: acc.deposit(50.0, "Bonus"))
                    .then_if(
                        condition=lambda acc: acc.get_transaction_count() >= 3,
                        then=lambda acc: {
                            **acc.get_account_summary(),
                            "account_status": "active_high_activity",
                            "eligible_for_premium": True,
                            "recommended_action": "upgrade_to_premium"
                        },
                        otherwise=lambda acc: {
                            **acc.get_account_summary(),
                            "account_status": "active_low_activity",
                            "eligible_for_premium": False
                        }
                    )
                ),
                otherwise=lambda acc_chain: (
                    Chain(acc_chain)
                    .then_map(lambda acc: {
                        **acc.get_account_summary(),
                        "account_status": "low_balance",
                        "eligible_for_premium": False,
                        "recommended_action": "deposit_funds"
                    })
                )
            )
        )

        assert result["account_number"] == "ACC-12345"
        assert result["balance"] == 1200.0  # 1000 + 250 - 100 + 50
        assert result["is_frozen"] is False
        assert result["overdraft_limit"] == 500.0
        assert result["transaction_count"] == 3  # deposit, withdraw, deposit (bonus)
        assert result["account_status"] == "active_high_activity"
        assert result["eligible_for_premium"] is True
        assert result["recommended_action"] == "upgrade_to_premium"

        # Verify last transaction
        last_transaction = result["last_transaction"]
        assert last_transaction["type"] == "deposit"
        assert last_transaction["amount"] == 50.0
        assert last_transaction["description"] == "Bonus"
        assert last_transaction["balance_after"] == 1200.0

    @pytest.mark.asyncio
    async def test_objects_with_custom_string_representations(self):
        """Test Chain() with objects that have custom __str__ and __repr__ methods.

        :raises AssertionError: If custom string representation operations don't work as expected.
        :return None: None
        """

        class ConfigurationManager:
            def __init__(self, env: str):
                self.environment = env
                self._settings = {}
                self._loaded = False

            def load_setting(self, key: str, value):
                self._settings[key] = value
                self._loaded = True
                return self

            def get_setting(self, key: str, default=None):
                return self._settings.get(key, default)

            def get_all_settings(self):
                return self._settings.copy()

            def is_loaded(self):
                return self._loaded

            def __str__(self):
                status = "loaded" if self._loaded else "empty"
                return f"Config[{self.environment}]({status}, {len(self._settings)} settings)"

            def __repr__(self):
                return f"ConfigurationManager(env='{self.environment}', settings={self._settings}, loaded={self._loaded})"

            def __eq__(self, other):
                if not isinstance(other, ConfigurationManager):
                    return False
                return (self.environment == other.environment and
                        self._settings == other._settings)

            def __hash__(self):
                return hash((self.environment, tuple(sorted(self._settings.items()))))

        # Create configuration instances
        dev_config = ConfigurationManager("development")
        dev_config.load_setting("debug", True).load_setting("db_host", "localhost")

        prod_config = ConfigurationManager("production")
        prod_config.load_setting("debug", False).load_setting("db_host", "prod-server")

        configs: list[ConfigurationManager]  = [dev_config, prod_config]

        result = await (
            Chain(configs)
            .then_foreach(
                transform=lambda config_chain: (
                    Chain(config_chain)
                    .then_map(lambda cfg: {
                        "environment": cfg.environment,
                        "settings": cfg.get_all_settings(),
                        "is_loaded": cfg.is_loaded(),
                        "str_representation": str(cfg),
                        "repr_representation": repr(cfg),
                        "setting_count": len(cfg.get_all_settings()),
                        "debug_enabled": cfg.get_setting("debug", False),
                        "database_host": cfg.get_setting("db_host", "unknown")
                    })
                )
            )
            .then_map(lambda config_list: {
                "configurations": config_list,
                "total_configs": len(config_list),
                "environments": [cfg["environment"] for cfg in config_list],
                "debug_configs": [cfg for cfg in config_list if cfg["debug_enabled"]],
                "production_configs": [cfg for cfg in config_list if not cfg["debug_enabled"]]
            })
        )

        assert result["total_configs"] == 2
        assert set(result["environments"]) == {"development", "production"}
        assert len(result["debug_configs"]) == 1
        assert len(result["production_configs"]) == 1

        # Verify development config
        dev_result = next(cfg for cfg in result["configurations"] if cfg["environment"] == "development")
        assert dev_result["debug_enabled"] is True
        assert dev_result["database_host"] == "localhost"
        assert dev_result["str_representation"] == "Config[development](loaded, 2 settings)"
        assert "ConfigurationManager(env='development'" in dev_result["repr_representation"]

        # Verify production config
        prod_result = next(cfg for cfg in result["configurations"] if cfg["environment"] == "production")
        assert prod_result["debug_enabled"] is False
        assert prod_result["database_host"] == "prod-server"
        assert prod_result["str_representation"] == "Config[production](loaded, 2 settings)"
        assert "ConfigurationManager(env='production'" in prod_result["repr_representation"]

