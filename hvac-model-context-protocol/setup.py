from setuptools import setup, find_packages

# Read version from package __init__.py
with open('hvac_mcp/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('"\'')
            break
    else:
        version = '0.0.1'

# Read description from README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='hvac-mcp',
    version=version,
    description='HVAC Model Context Protocol for enhancing LLM reasoning',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Organization',
    author_email='contact@yourorganization.com',
    url='https://github.com/your-org/hvac-model-context-protocol',
    packages=find_packages(),
    install_requires=[
        'typing; python_version < "3.5"',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    python_requires='>=3.7',
) 