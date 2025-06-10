# HF Papers Research Assistant

An AI-powered research assistant that helps you analyze and understand research papers using advanced language models and tools.

## Features

- 📚 Paper Analysis: Extract key insights from research papers
- 🤖 AI-Powered Summarization: Get concise summaries of complex papers
- 🔍 Smart Search: Find relevant papers and information quickly
- 📝 Note Generation: Create structured notes from papers
- 🎯 Research Crew: Collaborative AI agents for comprehensive research

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SriHarshitha88/hf-papers.git
cd hf-papers
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

1. Start the research assistant:
```bash
python src/main.py
```

2. Follow the interactive prompts to:
   - Upload papers
   - Generate summaries
   - Create research notes
   - Get insights and analysis

## Project Structure

```
hf-papers/
├── src/
│   ├── research_crew/     # AI research crew implementation
│   ├── tools/            # Custom research tools
│   └── main.py           # Main application entry point
├── tests/                # Test files
├── requirements.txt      # Project dependencies
└── README.md            # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Powered by OpenAI's GPT models
- Inspired by the need for better research paper analysis tools 