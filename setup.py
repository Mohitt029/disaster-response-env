from setuptools import setup, find_packages

setup(
    name="disaster-response-env",
    version="1.0.0",
    author="Mohit Singh",
    description="Multi-agent disaster response environment for RL training",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.0",
        "httpx>=0.25.0",
        "python-multipart>=0.0.6",
        "openai>=1.6.0",
        "requests>=2.31.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "plotly>=5.18.0",
        "streamlit>=1.28.0",
        "trl>=0.7.0",
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "accelerate>=0.25.0",
        "bitsandbytes>=0.41.0"
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "disaster-env=server.app:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)