# Multi-Participant AI Debate Platform

This is an **advanced AI-powered debate platform** that simulates academic debates with four distinct roles using different LLM models. The platform is powered by **litellm**, enabling seamless integration with any LLM provider (OpenAI, Anthropic, Ollama, etc.).

## Architecture

### Four Participants

1. **Organizer**: Provides a neutral 200-300 word overview of the topic without favoring any side
2. **Supporter**: Debater arguing in favor of the topic
3. **Opposer**: Debater arguing against the topic
4. **Judge**: Evaluates all arguments and provides detailed scoring

Each participant can use a **different LLM model** configured via litellm.

### Debate Flow

- **Round 0**: Organizer sets up the topic with neutral overview
- **Rounds 1-N**: Debaters alternate presenting arguments
  - Each debater receives the complete draft of the opponent's previous arguments
  - Debaters identify gaps, inconsistencies, logical fallacies, and unsupported claims
  - Rebuttals address specific weaknesses in opponent's arguments
- **Final Phase**: Judge evaluates all N arguments using a structured rubric:
  - Argument Quality (0-10)
  - Evidence Quality (0-10)
  - Logical Consistency (0-10)
  - Responsiveness to Gaps (0-10)
  - Overall Score (0-10)
  - Detailed Feedback

## Features

✅ **Multi-Model Support**: Use different LLM models for each participant via litellm
✅ **Intelligent Gap Analysis**: Debaters analyze opponent arguments for gaps and inconsistencies
✅ **Structured Judging**: Comprehensive scoring rubric with detailed feedback
✅ **Debate Transcripts**: Download complete debate records in JSON format
✅ **Configurable Rounds**: Run debates with 1-10 rounds
✅ **Easy UI**: Streamlit-based interface for configuration and monitoring

## Setup

### Prerequisites

- Python 3.8 or higher
- API keys for your chosen LLM providers (OpenAI, Claude, etc.)
- For local models: [Ollama](https://ollama.ai/) installed and running

### Install Dependencies

```bash
git clone https://github.com/your-username/ai-debate-platform.git
cd ai-debate-platform
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root with your API keys:

```env
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
# Add other provider keys as needed
```

### Running the App

```bash
streamlit run sl_debate.py
```

The app will open at `http://localhost:8501`

## Usage

1. **Enter the Debate Topic**: Provide the academic topic for debate
2. **Select LLM Models**: Choose a model for each participant (examples: `gpt-4`, `claude-3-opus`, `ollama/llama2`)
3. **Configure Participant Names**: Customize names for organizer, debaters, and judge
4. **Set Number of Rounds**: Choose how many debate rounds (1-10)
5. **Start the Debate**: Click "Start Debate" to begin
6. **Review Results**: See scoring and detailed feedback from the judge
7. **Download Transcript**: Export the complete debate as JSON

## Model Configuration Examples

| Provider | Model Format | Example |
|----------|--------------|---------|
| OpenAI | `gpt-3.5-turbo`, `gpt-4` | `gpt-4` |
| Anthropic | `claude-3-opus`, `claude-3-sonnet` | `claude-3-opus-20240229` |
| Ollama | `ollama/<model_name>` | `ollama/llama2` |
| Google | `gemini-pro` | `gemini-pro` |

## Example Debate

**Topic**: "Artificial Intelligence will have a net positive impact on employment"

1. **Moderator** provides balanced overview of AI and employment
2. **Debater A (GPT-4)** argues AI creates more jobs than it displaces
3. **Debater B (Claude)** counters with concerns about job displacement
4. Rounds continue with gap analysis and rebuttals
5. **Judge (Llama)** evaluates both sides comprehensively
6. Winner determined by overall score

## Data Models

### Argument
- `round_number`: Which round (0 for organizer)
- `participant_name`: Name of the speaker
- `participant_role`: "organizer", "supporter", "opposer", or "judge"
- `content`: The actual argument text
- `timestamp`: When the argument was generated
- `word_count`: Number of words in the argument
- `gaps_identified`: List of gaps/inconsistencies found in opponent's arguments

### Score
- `debater_name`: Name of evaluated debater
- `argument_quality`: 0-10 rating
- `evidence_quality`: 0-10 rating
- `logical_consistency`: 0-10 rating
- `responsiveness_to_gaps`: 0-10 rating
- `overall_score`: 0-10 rating
- `feedback`: Detailed evaluation feedback

