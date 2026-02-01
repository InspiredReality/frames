#!/usr/bin/env python3
"""Startup script for Railway deployment."""
import os
import subprocess
import sys

def main():
    """Start Gunicorn with proper PORT binding."""
    # Get PORT from environment (Railway sets this)
    port = os.environ.get('PORT', '5000')

    print(f"Starting Gunicorn on port {port}...")

    # Build gunicorn command
    workers = os.environ.get('WEB_CONCURRENCY', '1')
    cmd = [
        'gunicorn',
        'run:create_app()',
        '--bind', f'0.0.0.0:{port}',
        '--workers', workers,
        '--timeout', '120',
        '--preload',
        '--log-level', 'info',
        '--access-logfile', '-',
        '--error-logfile', '-'
    ]

    print(f"Command: {' '.join(cmd)}")

    # cmd
    print(f"Executed")

    # Execute gunicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Gunicorn: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
