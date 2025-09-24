#!/usr/bin/env python3
"""
Real-time Collaboration Service Test Suite
Tests the collaboration engine against <150ms latency requirement from Issue 001
"""

import asyncio
import json
import time
import websockets
import aiohttp
import logging
from datetime import datetime
from typing import Dict, Any, List
import statistics
import sys
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CollaborationServiceTest:
    """Test suite for real-time collaboration service."""
    
    def __init__(self, service_url: str = "http://localhost:8084", websocket_url: str = "ws://localhost:8084"):
        self.service_url = service_url
        self.websocket_url = websocket_url
        self.test_results = []
        
    async def test_service_health(self) -> Dict[str, Any]:
        """Test basic service health and availability."""
        logger.info("🏥 Testing service health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.service_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Service health: {data}")
                        return {"status": "healthy", "response": data}
                    else:
                        logger.error(f"❌ Service health check failed: {response.status}")
                        return {"status": "unhealthy", "status_code": response.status}
        except Exception as e:
            logger.error(f"❌ Service health check error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_session_management(self) -> Dict[str, Any]:
        """Test session creation and management."""
        logger.info("📋 Testing session management...")
        
        test_results = {
            "session_creation": False,
            "session_listing": False,
            "session_retrieval": False,
            "session_id": None
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test session creation
                create_payload = {
                    "document_id": f"test-doc-{int(time.time())}",
                    "max_participants": 5
                }
                
                async with session.post(
                    f"{self.service_url}/sessions",
                    json=create_payload
                ) as response:
                    if response.status == 200:
                        session_data = await response.json()
                        test_results["session_creation"] = True
                        test_results["session_id"] = session_data["session_id"]
                        logger.info(f"✅ Session created: {session_data['session_id']}")
                    else:
                        logger.error(f"❌ Session creation failed: {response.status}")
                        return test_results
                
                # Test session listing
                async with session.get(f"{self.service_url}/sessions") as response:
                    if response.status == 200:
                        sessions = await response.json()
                        test_results["session_listing"] = True
                        logger.info(f"✅ Session listing: {len(sessions)} sessions")
                    else:
                        logger.error(f"❌ Session listing failed: {response.status}")
                
                # Test session retrieval
                if test_results["session_id"]:
                    async with session.get(
                        f"{self.service_url}/sessions/{test_results['session_id']}"
                    ) as response:
                        if response.status == 200:
                            session_data = await response.json()
                            test_results["session_retrieval"] = True
                            logger.info(f"✅ Session retrieval: {session_data['session_id']}")
                        else:
                            logger.error(f"❌ Session retrieval failed: {response.status}")
                            
        except Exception as e:
            logger.error(f"❌ Session management test error: {e}")
            test_results["error"] = str(e)
        
        return test_results
    
    async def test_websocket_latency(self, session_id: str, num_messages: int = 10) -> Dict[str, Any]:
        """Test WebSocket latency to validate <150ms requirement."""
        logger.info(f"⚡ Testing WebSocket latency with {num_messages} messages...")
        
        latencies = []
        connection_successful = False
        messages_sent = 0
        messages_received = 0
        
        try:
            uri = f"{self.websocket_url}/ws/collaboration"
            
            async with websockets.connect(uri) as websocket:
                connection_successful = True
                logger.info("✅ WebSocket connection established")
                
                # Send join session message
                join_message = {
                    "type": "join_session",
                    "data": {
                        "session_id": session_id,
                        "user_id": f"test-user-{int(time.time())}",
                        "username": "Test User"
                    }
                }
                
                await websocket.send(json.dumps(join_message))
                
                # Wait for join confirmation
                join_response = await websocket.recv()
                logger.info(f"Join response: {join_response[:100]}...")
                
                # Send test messages and measure latency
                for i in range(num_messages):
                    start_time = time.time()
                    
                    test_message = {
                        "type": "document_update",
                        "data": {
                            "operation": "insert",
                            "position": i,
                            "content": f"Test message {i}",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    messages_sent += 1
                    
                    # Wait for echo/response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        end_time = time.time()
                        latency_ms = (end_time - start_time) * 1000
                        latencies.append(latency_ms)
                        messages_received += 1
                        
                        logger.debug(f"Message {i}: {latency_ms:.1f}ms")
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"Message {i}: Timeout waiting for response")
                        
                    # Small delay between messages
                    await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"❌ WebSocket latency test error: {e}")
            return {
                "connection_successful": connection_successful,
                "error": str(e)
            }
        
        # Calculate statistics
        if latencies:
            stats = {
                "mean_latency_ms": statistics.mean(latencies),
                "median_latency_ms": statistics.median(latencies),
                "p95_latency_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99_latency_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "std_latency_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0.0
            }
        else:
            stats = {}
        
        # Check <150ms requirement
        meets_requirement = stats.get("p95_latency_ms", float('inf')) < 150.0
        
        results = {
            "connection_successful": connection_successful,
            "messages_sent": messages_sent,
            "messages_received": messages_received,
            "latencies": latencies,
            "statistics": stats,
            "meets_150ms_requirement": meets_requirement,
            "requirement_status": "PASS" if meets_requirement else "FAIL"
        }
        
        logger.info(f"Latency test results:")
        logger.info(f"  Messages sent/received: {messages_sent}/{messages_received}")
        if stats:
            logger.info(f"  Mean latency: {stats['mean_latency_ms']:.1f}ms")
            logger.info(f"  P95 latency: {stats['p95_latency_ms']:.1f}ms")
            logger.info(f"  Max latency: {stats['max_latency_ms']:.1f}ms")
            logger.info(f"  <150ms requirement: {'✅ PASS' if meets_requirement else '❌ FAIL'}")
        
        return results
    
    async def test_concurrent_connections(self, session_id: str, num_connections: int = 5) -> Dict[str, Any]:
        """Test concurrent WebSocket connections and message broadcasting."""
        logger.info(f"👥 Testing {num_connections} concurrent connections...")
        
        connections = []
        connection_results = []
        
        async def create_connection(user_id: str) -> Dict[str, Any]:
            """Create a single WebSocket connection."""
            try:
                uri = f"{self.websocket_url}/ws/collaboration"
                
                websocket = await websockets.connect(uri)
                
                # Send join message
                join_message = {
                    "type": "join_session",
                    "data": {
                        "session_id": session_id,
                        "user_id": user_id,
                        "username": f"User {user_id}"
                    }
                }
                
                await websocket.send(json.dumps(join_message))
                join_response = await websocket.recv()
                
                return {
                    "user_id": user_id,
                    "websocket": websocket,
                    "connected": True,
                    "join_response": join_response
                }
                
            except Exception as e:
                logger.error(f"Failed to create connection for {user_id}: {e}")
                return {
                    "user_id": user_id,
                    "connected": False,
                    "error": str(e)
                }
        
        try:
            # Create concurrent connections
            tasks = [
                create_connection(f"test-user-{i}")
                for i in range(num_connections)
            ]
            
            connection_results = await asyncio.gather(*tasks)
            
            # Filter successful connections
            successful_connections = [
                result for result in connection_results
                if result.get("connected", False)
            ]
            
            logger.info(f"✅ Established {len(successful_connections)}/{num_connections} connections")
            
            # Test message broadcasting
            if successful_connections:
                # Send a message from the first user
                sender = successful_connections[0]
                broadcast_message = {
                    "type": "document_update",
                    "data": {
                        "operation": "insert",
                        "content": "Broadcast test message",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                send_time = time.time()
                await sender["websocket"].send(json.dumps(broadcast_message))
                
                # Listen for messages on other connections
                message_times = []
                for connection in successful_connections[1:]:  # Skip sender
                    try:
                        response = await asyncio.wait_for(
                            connection["websocket"].recv(),
                            timeout=2.0
                        )
                        receive_time = time.time()
                        broadcast_latency = (receive_time - send_time) * 1000
                        message_times.append(broadcast_latency)
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"User {connection['user_id']} did not receive broadcast")
                
                # Clean up connections
                for connection in successful_connections:
                    try:
                        await connection["websocket"].close()
                    except:
                        pass
                
                return {
                    "total_connections": num_connections,
                    "successful_connections": len(successful_connections),
                    "broadcast_test": True,
                    "broadcast_latencies_ms": message_times,
                    "avg_broadcast_latency_ms": statistics.mean(message_times) if message_times else 0,
                    "connection_success_rate": len(successful_connections) / num_connections * 100
                }
            
            else:
                return {
                    "total_connections": num_connections,
                    "successful_connections": 0,
                    "broadcast_test": False,
                    "error": "No successful connections established"
                }
                
        except Exception as e:
            # Clean up any open connections
            for result in connection_results:
                if result.get("websocket"):
                    try:
                        await result["websocket"].close()
                    except:
                        pass
            
            logger.error(f"❌ Concurrent connections test error: {e}")
            return {
                "error": str(e),
                "total_connections": num_connections,
                "successful_connections": 0
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all collaboration service tests."""
        logger.info("🚀 Starting Comprehensive Collaboration Service Test")
        logger.info("=" * 60)
        
        overall_results = {
            "timestamp": datetime.now().isoformat(),
            "service_url": self.service_url,
            "websocket_url": self.websocket_url,
            "tests": {}
        }
        
        # Test 1: Service Health
        health_result = await self.test_service_health()
        overall_results["tests"]["health"] = health_result
        
        if health_result["status"] != "healthy":
            logger.error("❌ Service health check failed, skipping other tests")
            overall_results["overall_status"] = "FAIL"
            overall_results["reason"] = "Service not healthy"
            return overall_results
        
        # Test 2: Session Management
        session_result = await self.test_session_management()
        overall_results["tests"]["session_management"] = session_result
        
        session_id = session_result.get("session_id")
        if not session_id:
            logger.error("❌ Session creation failed, skipping WebSocket tests")
            overall_results["overall_status"] = "FAIL"
            overall_results["reason"] = "Session creation failed"
            return overall_results
        
        # Test 3: WebSocket Latency (Critical requirement)
        latency_result = await self.test_websocket_latency(session_id, num_messages=20)
        overall_results["tests"]["websocket_latency"] = latency_result
        
        # Test 4: Concurrent Connections
        concurrent_result = await self.test_concurrent_connections(session_id, num_connections=5)
        overall_results["tests"]["concurrent_connections"] = concurrent_result
        
        # Determine overall status
        health_ok = health_result["status"] == "healthy"
        session_ok = session_result["session_creation"] and session_result["session_listing"]
        latency_ok = latency_result.get("meets_150ms_requirement", False)
        concurrent_ok = concurrent_result.get("successful_connections", 0) > 0
        
        if health_ok and session_ok and latency_ok and concurrent_ok:
            overall_results["overall_status"] = "PASS"
            overall_results["reason"] = "All tests passed"
        else:
            overall_results["overall_status"] = "FAIL"
            failures = []
            if not health_ok:
                failures.append("health")
            if not session_ok:
                failures.append("session_management")
            if not latency_ok:
                failures.append("latency_requirement")
            if not concurrent_ok:
                failures.append("concurrent_connections")
            overall_results["reason"] = f"Failed tests: {', '.join(failures)}"
        
        # Summary
        logger.info(f"\n📊 Test Summary:")
        logger.info(f"  Service Health: {'✅' if health_ok else '❌'}")
        logger.info(f"  Session Management: {'✅' if session_ok else '❌'}")
        logger.info(f"  <150ms Latency: {'✅' if latency_ok else '❌'}")
        logger.info(f"  Concurrent Connections: {'✅' if concurrent_ok else '❌'}")
        logger.info(f"  Overall Status: {overall_results['overall_status']}")
        
        if latency_result.get("statistics"):
            stats = latency_result["statistics"]
            logger.info(f"\n⚡ Latency Performance:")
            logger.info(f"  P95 Latency: {stats['p95_latency_ms']:.1f}ms (requirement: <150ms)")
            logger.info(f"  Mean Latency: {stats['mean_latency_ms']:.1f}ms")
            logger.info(f"  Max Latency: {stats['max_latency_ms']:.1f}ms")
        
        return overall_results


async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='Test real-time collaboration service')
    parser.add_argument('--service-url', default='http://localhost:8084', help='Collaboration service URL')
    parser.add_argument('--websocket-url', default='ws://localhost:8084', help='WebSocket URL')
    parser.add_argument('--output', help='Output JSON file for results')
    
    args = parser.parse_args()
    
    tester = CollaborationServiceTest(
        service_url=args.service_url,
        websocket_url=args.websocket_url
    )
    
    try:
        results = await tester.run_comprehensive_test()
        
        # Save results if output file specified
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"📁 Results saved to: {output_path}")
        
        # Return appropriate exit code
        return 0 if results["overall_status"] == "PASS" else 1
        
    except Exception as e:
        logger.error(f"❌ Test execution error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))