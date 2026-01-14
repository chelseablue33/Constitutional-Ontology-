# Streamlit Secrets Configuration

## Setup Instructions

1. **Copy the example file:**
   ```bash
   cp secrets.toml.example secrets.toml
   ```

2. **Edit `secrets.toml` and add your OpenAI API key:**
   ```toml
   [openai]
   api_key = "sk-your-actual-api-key-here"
   ```

3. **Get your API key from:**
   https://platform.openai.com/api-keys

4. **Restart your Streamlit app** after creating/updating `secrets.toml`

## Security Note

- **Never commit `secrets.toml` to version control**
- The `.gitignore` should exclude `secrets.toml`
- Only commit `secrets.toml.example` as a template

## Alternative: Environment Variable

You can also set the API key as an environment variable:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```
