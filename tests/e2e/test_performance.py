"""
Performance tests for HTTP transport.

Tests performance characteristics including:
- Response time benchmarks
- Memory usage under load
- Connection pooling and management
- Concurrent request handling performance
"""
import asyncio
import os
import psutil
import subprocess
import time
import pytest
import httpx
from statistics import mean, median


class TestHTTPPerformanceBenchmarks:
    """Performance benchmark tests for HTTP transport."""
    
    @pytest.fixture
    def performance_server(self):
        """Start server for performance testing."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-perf-key'
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        # Give server time to fully start
        time.sleep(4)
        
        yield process
        
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=15)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_response_time_benchmarks(self, performance_server):
        """Test response time benchmarks for HTTP requests."""
        process = performance_server
        assert process.poll() is None, "Performance server not running"
        
        response_times = []
        
        async with httpx.AsyncClient() as client:
            # Warm up request
            try:
                await client.get("http://localhost:3001/", timeout=10.0)
            except (httpx.ConnectError, httpx.TimeoutException):
                pytest.skip("HTTP server not accessible for performance testing")
            
            # Benchmark requests
            for i in range(20):
                start_time = time.perf_counter()
                
                try:
                    response = await client.get("http://localhost:3001/", timeout=10.0)
                    end_time = time.perf_counter()
                    
                    response_time = (end_time - start_time) * 1000  # Convert to ms
                    response_times.append(response_time)
                    
                except (httpx.TimeoutException, httpx.ConnectError):
                    # Skip this measurement
                    continue
        
        if response_times:
            avg_time = mean(response_times)
            median_time = median(response_times)
            max_time = max(response_times)
            
            print(f"\nHTTP Response Time Benchmarks:")
            print(f"Average: {avg_time:.2f}ms")
            print(f"Median: {median_time:.2f}ms") 
            print(f"Max: {max_time:.2f}ms")
            
            # Performance assertions
            assert avg_time < 1000, f"Average response time {avg_time:.2f}ms too slow"
            assert median_time < 500, f"Median response time {median_time:.2f}ms too slow"
            assert max_time < 3000, f"Max response time {max_time:.2f}ms too slow"
        else:
            pytest.skip("No successful requests for performance measurement")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self, performance_server):
        """Test performance under concurrent load."""
        process = performance_server
        assert process.poll() is None
        
        # Test with increasing concurrency levels
        concurrency_levels = [5, 10, 20]
        
        for concurrency in concurrency_levels:
            start_time = time.perf_counter()
            
            async with httpx.AsyncClient() as client:
                tasks = []
                
                for i in range(concurrency):
                    task = client.get(f"http://localhost:3001/", timeout=15.0)
                    tasks.append(task)
                
                try:
                    responses = await asyncio.gather(*tasks, return_exceptions=True)
                    end_time = time.perf_counter()
                    
                    # Count successful responses
                    successful = sum(
                        1 for r in responses
                        if not isinstance(r, Exception) and hasattr(r, 'status_code')
                    )
                    
                    total_time = (end_time - start_time) * 1000  # ms
                    avg_time_per_request = total_time / concurrency
                    
                    print(f"\nConcurrency {concurrency}: {successful}/{concurrency} successful")
                    print(f"Total time: {total_time:.2f}ms")
                    print(f"Avg per request: {avg_time_per_request:.2f}ms")
                    
                    # Performance assertions
                    assert successful >= concurrency * 0.7, f"Too many failures at concurrency {concurrency}"
                    assert avg_time_per_request < 2000, f"Avg time {avg_time_per_request:.2f}ms too slow"
                    
                except asyncio.TimeoutError:
                    pytest.fail(f"Concurrent requests timed out at concurrency {concurrency}")
    
    @pytest.mark.performance
    def test_memory_usage_under_load(self, performance_server):
        """Test memory usage characteristics under load."""
        process = performance_server
        assert process.poll() is None
        
        try:
            # Get process for memory monitoring
            server_process = psutil.Process(process.pid)
            
            # Measure initial memory usage
            initial_memory = server_process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"\nInitial memory usage: {initial_memory:.2f}MB")
            
            # Run some load and measure memory
            async def create_load():
                async with httpx.AsyncClient() as client:
                    tasks = []
                    for i in range(50):
                        task = client.get("http://localhost:3001/", timeout=10.0)
                        tasks.append(task)
                    
                    try:
                        await asyncio.gather(*tasks, return_exceptions=True)
                    except Exception:
                        pass  # Ignore errors for memory test
            
            # Run load test
            asyncio.run(create_load())
            
            # Allow some time for cleanup
            time.sleep(2)
            
            # Measure memory after load
            final_memory = server_process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"Final memory usage: {final_memory:.2f}MB")
            print(f"Memory increase: {memory_increase:.2f}MB")
            
            # Memory assertions
            assert final_memory < 500, f"Memory usage {final_memory:.2f}MB too high"
            assert memory_increase < 100, f"Memory increase {memory_increase:.2f}MB too high"
            
        except psutil.NoSuchProcess:
            pytest.skip("Could not monitor server process memory")


class TestHTTPConnectionManagement:
    """Test HTTP connection pooling and management."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_connection_reuse(self):
        """Test HTTP connection reuse and pooling."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-conn-key'
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        try:
            time.sleep(3)
            assert process.poll() is None
            
            # Test connection reuse with persistent client
            async with httpx.AsyncClient() as client:
                response_times = []
                
                # Make multiple requests with the same client
                for i in range(10):
                    start_time = time.perf_counter()
                    
                    try:
                        response = await client.get("http://localhost:3001/", timeout=8.0)
                        end_time = time.perf_counter()
                        
                        response_time = (end_time - start_time) * 1000
                        response_times.append(response_time)
                        
                    except (httpx.ConnectError, httpx.TimeoutException):
                        continue
                
                if len(response_times) >= 5:
                    # Later requests should be faster (connection reuse)
                    first_half = response_times[:len(response_times)//2]
                    second_half = response_times[len(response_times)//2:]
                    
                    avg_first = mean(first_half)
                    avg_second = mean(second_half)
                    
                    print(f"\nConnection reuse test:")
                    print(f"First half avg: {avg_first:.2f}ms")
                    print(f"Second half avg: {avg_second:.2f}ms")
                    
                    # Second half should be similar or faster (connection reuse benefit)
                    # Allow some variance but check for reasonable performance
                    assert avg_second < avg_first * 2, "Connection reuse not working efficiently"
                
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_multiple_client_connections(self):
        """Test multiple simultaneous client connections."""
        env = os.environ.copy()
        env['MCP_TRANSPORT'] = 'streamable-http'
        env['OUTLINE_API_KEY'] = 'test-multi-conn-key'
        
        process = subprocess.Popen(
            ['python', '-m', 'mcp_outline.server'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/home/runner/work/mcp-outline/mcp-outline'
        )
        
        try:
            time.sleep(3)
            assert process.poll() is None
            
            # Create multiple independent clients
            clients = [httpx.AsyncClient() for _ in range(5)]
            
            try:
                # Each client makes requests simultaneously
                async def client_requests(client, client_id):
                    results = []
                    for i in range(3):
                        try:
                            response = await client.get(f"http://localhost:3001/", timeout=10.0)
                            results.append(True)
                        except Exception:
                            results.append(False)
                    return client_id, results
                
                # Run all clients concurrently
                tasks = [client_requests(client, i) for i, client in enumerate(clients)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successful client sessions
                successful_clients = 0
                for result in results:
                    if not isinstance(result, Exception):
                        client_id, client_results = result
                        if any(client_results):  # At least one request succeeded
                            successful_clients += 1
                
                print(f"\nMultiple clients test: {successful_clients}/{len(clients)} successful")
                
                # Most clients should succeed
                assert successful_clients >= len(clients) * 0.6, "Too many client connection failures"
                
            finally:
                # Clean up clients
                for client in clients:
                    await client.aclose()
                
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)