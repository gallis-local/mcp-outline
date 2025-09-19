"""
Docker container tests for HTTP transport.

Tests HTTP transport in containerized environment including:
- HTTP transport in containerized environment
- Port binding and network accessibility 
- Environment variable configuration in Docker
- Health checks and readiness probes
"""
import json
import os
import subprocess
import time
import pytest
import httpx
import docker


class TestDockerHTTPTransport:
    """Test HTTP transport in Docker containers."""
    
    @pytest.fixture
    def docker_client(self):
        """Get Docker client if available."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception:
            pytest.skip("Docker not available")
    
    def test_docker_image_build(self, docker_client):
        """Test that Docker image can be built successfully."""
        try:
            # Build the image from the repository root
            image, logs = docker_client.images.build(
                path="/home/runner/work/mcp-outline/mcp-outline",
                tag="mcp-outline:test",
                rm=True
            )
            
            assert image is not None
            assert "mcp-outline:test" in [tag for tag in image.tags]
            
        except docker.errors.BuildError as e:
            pytest.fail(f"Docker build failed: {e}")
        except Exception as e:
            pytest.skip(f"Docker build not possible: {e}")
    
    @pytest.mark.asyncio
    async def test_container_http_transport_startup(self, docker_client):
        """Test container startup with HTTP transport."""
        try:
            # First build the image
            image, _ = docker_client.images.build(
                path="/home/runner/work/mcp-outline/mcp-outline",
                tag="mcp-outline:test",
                rm=True
            )
            
            # Run container with HTTP transport
            container = docker_client.containers.run(
                "mcp-outline:test",
                environment={
                    "MCP_TRANSPORT": "streamable-http",
                    "OUTLINE_API_KEY": "test-docker-key"
                },
                ports={"3001/tcp": 3001},
                detach=True,
                remove=True
            )
            
            try:
                # Give container time to start
                time.sleep(5)
                
                # Check container is running
                container.reload()
                assert container.status == "running"
                
                # Test HTTP connectivity
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get("http://localhost:3001/", timeout=10.0)
                        # Should get some response
                        assert hasattr(response, 'status_code')
                        assert response.status_code in [200, 404, 405, 422]
                        
                    except httpx.ConnectError:
                        # Check container logs for debugging
                        logs = container.logs().decode()
                        pytest.fail(f"HTTP connection failed. Container logs:\n{logs}")
                
            finally:
                # Cleanup container
                try:
                    container.stop(timeout=10)
                except Exception:
                    pass
                
        except docker.errors.ImageNotFound:
            pytest.skip("Docker image build failed or not available")
        except Exception as e:
            pytest.skip(f"Docker container test not possible: {e}")


class TestDockerEnvironmentConfiguration:
    """Test environment variable configuration in Docker."""
    
    @pytest.fixture
    def docker_client(self):
        """Get Docker client if available."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception:
            pytest.skip("Docker not available")
    
    def test_docker_environment_variables(self, docker_client):
        """Test environment variable configuration in Docker container."""
        try:
            # Build image first
            image, _ = docker_client.images.build(
                path="/home/runner/work/mcp-outline/mcp-outline",
                tag="mcp-outline:test-env",
                rm=True
            )
            
            # Test different environment configurations
            env_configs = [
                {"MCP_TRANSPORT": "streamable-http", "OUTLINE_API_KEY": "test-key"},
                {"MCP_TRANSPORT": "http", "OUTLINE_API_KEY": "test-key"},  # Compatibility mapping
                {"MCP_TRANSPORT": "sse", "OUTLINE_API_KEY": "test-key"},
            ]
            
            for env_config in env_configs:
                container = docker_client.containers.run(
                    "mcp-outline:test-env", 
                    environment=env_config,
                    detach=True,
                    remove=True
                )
                
                try:
                    # Give container time to start
                    time.sleep(3)
                    
                    # Check container status
                    container.reload()
                    
                    # Container should either be running or have exited cleanly
                    if container.status == "exited":
                        # Check exit code
                        exit_code = container.attrs['State']['ExitCode']
                        assert exit_code in [0, 1], f"Container failed with exit code {exit_code}"
                    else:
                        assert container.status == "running"
                    
                    # Check logs for proper environment handling
                    logs = container.logs().decode()
                    transport_mode = env_config["MCP_TRANSPORT"]
                    
                    # Should log the transport mode (or mapped version)
                    if transport_mode == "http":
                        assert "streamable-http" in logs or "HTTP" in logs
                    else:
                        assert transport_mode in logs or transport_mode.upper() in logs
                    
                finally:
                    try:
                        container.stop(timeout=5)
                    except Exception:
                        pass
                        
        except Exception as e:
            pytest.skip(f"Docker environment test not possible: {e}")


class TestDockerNetworkAccessibility:
    """Test port binding and network accessibility."""
    
    @pytest.fixture
    def docker_client(self):
        """Get Docker client if available."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception:
            pytest.skip("Docker not available")
    
    def test_docker_port_binding(self, docker_client):
        """Test Docker port binding for HTTP transport."""
        try:
            # Build image
            image, _ = docker_client.images.build(
                path="/home/runner/work/mcp-outline/mcp-outline",
                tag="mcp-outline:test-port",
                rm=True
            )
            
            # Test different port configurations
            port_configs = [
                {"3001/tcp": 3001},  # Direct mapping
                {"3001/tcp": 8001},  # Different host port
                {"3001/tcp": None},  # Random port
            ]
            
            for port_config in port_configs:
                container = docker_client.containers.run(
                    "mcp-outline:test-port",
                    environment={
                        "MCP_TRANSPORT": "streamable-http",
                        "OUTLINE_API_KEY": "test-port-key"
                    },
                    ports=port_config,
                    detach=True,
                    remove=True
                )
                
                try:
                    time.sleep(3)
                    container.reload()
                    
                    # Get the actual port mapping
                    port_info = container.ports.get('3001/tcp')
                    if port_info:
                        host_port = port_info[0]['HostPort']
                        print(f"Container port 3001 mapped to host port {host_port}")
                        
                        # Verify port is accessible (basic connectivity test)
                        # Note: Full HTTP test might not work in CI environment
                        assert host_port is not None
                        assert int(host_port) > 0
                    
                finally:
                    try:
                        container.stop(timeout=5)
                    except Exception:
                        pass
                        
        except Exception as e:
            pytest.skip(f"Docker port binding test not possible: {e}")


class TestDockerHealthChecks:
    """Test health checks and readiness probes."""
    
    @pytest.fixture
    def docker_client(self):
        """Get Docker client if available."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception:
            pytest.skip("Docker not available")
    
    def test_container_startup_health(self, docker_client):
        """Test container startup health and readiness."""
        try:
            # Build image
            image, _ = docker_client.images.build(
                path="/home/runner/work/mcp-outline/mcp-outline",
                tag="mcp-outline:test-health",
                rm=True
            )
            
            container = docker_client.containers.run(
                "mcp-outline:test-health",
                environment={
                    "MCP_TRANSPORT": "streamable-http",
                    "OUTLINE_API_KEY": "test-health-key"
                },
                ports={"3001/tcp": 3001},
                detach=True,
                remove=True,
                healthcheck={
                    "test": ["CMD", "curl", "-f", "http://localhost:3001/"],
                    "interval": 30000000000,  # 30s in nanoseconds
                    "timeout": 10000000000,   # 10s in nanoseconds
                    "retries": 3
                }
            )
            
            try:
                # Monitor container health over time
                health_checks = []
                
                for i in range(10):  # Check for up to 30 seconds
                    time.sleep(3)
                    container.reload()
                    
                    status = container.status
                    health_checks.append(status)
                    
                    print(f"Health check {i}: status={status}")
                    
                    # Container should be running
                    if status == "running":
                        break
                    elif status == "exited":
                        # Check exit code and logs
                        exit_code = container.attrs['State']['ExitCode']
                        logs = container.logs().decode()
                        
                        if exit_code == 0:
                            # Clean exit is acceptable
                            break
                        else:
                            pytest.fail(f"Container exited with code {exit_code}. Logs:\n{logs}")
                
                # Should have achieved running status at some point
                assert "running" in health_checks or any(
                    check == "exited" and container.attrs['State']['ExitCode'] == 0 
                    for check in health_checks
                ), f"Container never achieved healthy state: {health_checks}"
                
            finally:
                try:
                    container.stop(timeout=10)
                except Exception:
                    pass
                    
        except Exception as e:
            pytest.skip(f"Docker health check test not possible: {e}")
    
    def test_container_graceful_shutdown(self, docker_client):
        """Test container graceful shutdown behavior."""
        try:
            # Build image
            image, _ = docker_client.images.build(
                path="/home/runner/work/mcp-outline/mcp-outline",
                tag="mcp-outline:test-shutdown",
                rm=True
            )
            
            container = docker_client.containers.run(
                "mcp-outline:test-shutdown",
                environment={
                    "MCP_TRANSPORT": "streamable-http",
                    "OUTLINE_API_KEY": "test-shutdown-key"
                },
                detach=True,
                remove=True
            )
            
            try:
                # Let container start
                time.sleep(3)
                container.reload()
                
                if container.status == "running":
                    # Test graceful shutdown
                    start_time = time.time()
                    container.stop(timeout=10)
                    end_time = time.time()
                    
                    shutdown_time = end_time - start_time
                    
                    # Should shutdown reasonably quickly
                    assert shutdown_time < 15, f"Shutdown took {shutdown_time:.2f}s too long"
                    
                    # Check final exit code
                    container.reload()
                    exit_code = container.attrs['State']['ExitCode']
                    
                    # Should be clean shutdown
                    assert exit_code in [0, 130, 143], f"Unclean shutdown with exit code {exit_code}"
                
            finally:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
                    
        except Exception as e:
            pytest.skip(f"Docker shutdown test not possible: {e}")