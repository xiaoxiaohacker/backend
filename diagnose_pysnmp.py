import sys
import importlib
import inspect

print("Python version:", sys.version)
print("\nChecking pysnmp installation...")

# Try to import pysnmp and check version
try:
    import pysnmp
    print(f"pysnmp version: {pysnmp.__version__}")
except ImportError:
    print("ERROR: pysnmp not installed!")
    sys.exit(1)

# Print module paths
print("\nModule paths:")
print(f"pysnmp: {pysnmp.__file__}")

try:
    import pysnmp.hlapi
    print(f"pysnmp.hlapi: {pysnmp.hlapi.__file__}")
except ImportError as e:
    print(f"Failed to import pysnmp.hlapi: {e}")

try:
    import pysnmp.hlapi.v3arch
    print(f"pysnmp.hlapi.v3arch: {pysnmp.hlapi.v3arch.__file__}")
except ImportError as e:
    print(f"Failed to import pysnmp.hlapi.v3arch: {e}")

try:
    import pysnmp.hlapi.v3arch.asyncio
    print(f"pysnmp.hlapi.v3arch.asyncio: {pysnmp.hlapi.v3arch.asyncio.__file__}")
except ImportError as e:
    print(f"Failed to import pysnmp.hlapi.v3arch.asyncio: {e}")

try:
    import pysnmp.hlapi.v3arch.asyncio.cmdgen
    print(f"pysnmp.hlapi.v3arch.asyncio.cmdgen: {pysnmp.hlapi.v3arch.asyncio.cmdgen.__file__}")
except ImportError as e:
    print(f"Failed to import pysnmp.hlapi.v3arch.asyncio.cmdgen: {e}")

# Check what's available in each module
print("\n--- Available attributes in pysnmp.hlapi ---")
try:
    import pysnmp.hlapi
    print(dir(pysnmp.hlapi))
except ImportError:
    print("Could not list attributes")

print("\n--- Available attributes in pysnmp.hlapi.v3arch ---")
try:
    import pysnmp.hlapi.v3arch
    print(dir(pysnmp.hlapi.v3arch))
except ImportError:
    print("Could not list attributes")

print("\n--- Available attributes in pysnmp.hlapi.v3arch.asyncio.cmdgen ---")
try:
    import pysnmp.hlapi.v3arch.asyncio.cmdgen
    print(dir(pysnmp.hlapi.v3arch.asyncio.cmdgen))
except ImportError:
    print("Could not list attributes")

# Try direct imports
print("\n--- Testing direct imports ---")
try:
    from pysnmp.hlapi.v3arch import SnmpEngine
    print("Successfully imported SnmpEngine from pysnmp.hlapi.v3arch")
except ImportError as e:
    print(f"Failed to import SnmpEngine from pysnmp.hlapi.v3arch: {e}")

try:
    from pysnmp.hlapi.v3arch import CommunityData
    print("Successfully imported CommunityData from pysnmp.hlapi.v3arch")
except ImportError as e:
    print(f"Failed to import CommunityData from pysnmp.hlapi.v3arch: {e}")

try:
    from pysnmp.hlapi.v3arch import UdpTransportTarget
    print("Successfully imported UdpTransportTarget from pysnmp.hlapi.v3arch")
except ImportError as e:
    print(f"Failed to import UdpTransportTarget from pysnmp.hlapi.v3arch: {e}")

try:
    from pysnmp.hlapi.v3arch import ContextData, ObjectType, ObjectIdentity
    print("Successfully imported ContextData, ObjectType, ObjectIdentity from pysnmp.hlapi.v3arch")
except ImportError as e:
    print(f"Failed to import ContextData, ObjectType, ObjectIdentity from pysnmp.hlapi.v3arch: {e}")

try:
    from pysnmp.hlapi.v3arch.asyncio.cmdgen import getCmd, nextCmd
    print("Successfully imported getCmd, nextCmd from pysnmp.hlapi.v3arch.asyncio.cmdgen")
except ImportError as e:
    print(f"Failed to import getCmd, nextCmd from pysnmp.hlapi.v3arch.asyncio.cmdgen: {e}")

# Check for circular imports
print("\n--- Checking for circular imports in snmp.py ---")
try:
    import app.adapters.snmp
    print("Successfully imported app.adapters.snmp module")
except ImportError as e:
    print(f"Failed to import app.adapters.snmp: {e}")
    import traceback
    traceback.print_exc()

print("\nDiagnosis complete.")