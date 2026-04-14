"""
Patch: adiciona vault tools (search_vault + read_vault_note) nos agentes.
Regras:
  - SOMENTE LEITURA em todas as camadas
  - Escopo por agente
  - path traversal bloqueado no vault_lib.py
  - Docker mount :ro já configurado no docker-compose.yml
"""
import re

def patch_james():
    p = '/opt/claudeserver/agents/james/main.py'
    s = open(p).read()
    if 'import vault_lib' not in s:
        s = s.replace(
            'from fastapi import FastAPI, HTTPException',
            'import sys\nsys.path.insert(0, "/app/obsidian")\nimport vault_lib\n\nfrom fastapi import FastAPI, HTTPException'
        )
    if 'AGENT_NAME' not in s:
        s = s.replace('MAX_HISTORY    = 20', 'MAX_HISTORY    = 20\nAGENT_NAME     = "james"')
    if 'search_vault' not in s:
        s = s.replace(']\n\n# -- Agent Caller', '] + vault_lib.get_tools_anthropic(AGENT_NAME)\n\n# -- Agent Caller')
    if 'vault_lib.search_vault' not in s:
        s = s.replace(
            '    return f"[ERRO] Tool desconhecida: {tool_name}"',
            '    if tool_name == "search_vault": return str(vault_lib.search_vault(AGENT_NAME, tool_input.get("query", "")))\n'
            '    if tool_name == "read_vault_note": return str(vault_lib.read_vault_note(AGENT_NAME, tool_input.get("path", "")))\n'
            '    return f"[ERRO] Tool desconhecida: {tool_name}"'
        )
    open(p, 'w').write(s)
    print(f'james: OK search_vault={("search_vault" in s)} import={("vault_lib" in s)}')

def patch_rick():
    p = '/opt/claudeserver/agents/rick/main.py'
    s = open(p).read()
    if 'import vault_lib' not in s:
        s = s.replace(
            'from fastapi import FastAPI, HTTPException',
            'import sys\nsys.path.insert(0, "/app/obsidian")\nimport vault_lib\n\nfrom fastapi import FastAPI, HTTPException'
        )
    if 'AGENT_NAME' not in s:
        s = s.replace(
            'MAX_TOKENS     = int(os.environ.get("MAX_TOKENS", "4096"))',
            'MAX_TOKENS     = int(os.environ.get("MAX_TOKENS", "4096"))\nAGENT_NAME     = "rick"'
        )
    if 'search_vault' not in s:
        s = re.sub(r'(ANTHROPIC_TOOLS\s*=\s*\[.*?\])', r'\1 + vault_lib.get_tools_anthropic(AGENT_NAME)', s, flags=re.DOTALL)
    if 'vault_lib.search_vault' not in s:
        # Find last "unknown tool" return in _dispatch_tool
        s = s.replace(
            '    return f"[ERRO] Tool desconhecida: {tool_name}"',
            '    if tool_name == "search_vault": return str(vault_lib.search_vault(AGENT_NAME, tool_input.get("query", "")))\n'
            '    if tool_name == "read_vault_note": return str(vault_lib.read_vault_note(AGENT_NAME, tool_input.get("path", "")))\n'
            '    return f"[ERRO] Tool desconhecida: {tool_name}"',
            1
        )
    open(p, 'w').write(s)
    print(f'rick:  OK search_vault={("search_vault" in s)} import={("vault_lib" in s)}')

def patch_regi():
    p = '/opt/claudeserver/agents/regi/main.py'
    s = open(p).read()
    if 'import vault_lib' not in s:
        s = s.replace(
            'from fastapi import FastAPI, HTTPException',
            'import sys\nsys.path.insert(0, "/app/obsidian")\nimport vault_lib\n\nfrom fastapi import FastAPI, HTTPException'
        )
    if 'AGENT_NAME' not in s:
        s = s.replace(
            'MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4096"))',
            'MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4096"))\nAGENT_NAME = "regi"'
        )
    if 'search_vault' not in s:
        s = re.sub(r'(TOOLS\s*=\s*\[.*?\])', r'\1 + vault_lib.get_tools_openai(AGENT_NAME)', s, flags=re.DOTALL)
    if 'vault_lib.search_vault' not in s:
        s = s.replace(
            '"wait_for_healthy":  lambda a:',
            '"search_vault":      lambda a: vault_lib.search_vault(AGENT_NAME, a.get("query", "")),\n'
            '    "read_vault_note":   lambda a: vault_lib.read_vault_note(AGENT_NAME, a.get("path", "")),\n'
            '    "wait_for_healthy":  lambda a:'
        )
    open(p, 'w').write(s)
    print(f'regi:  OK search_vault={("search_vault" in s)} import={("vault_lib" in s)}')

def patch_mark():
    p = '/opt/claudeserver/agents/mark/main.py'
    s = open(p).read()
    if 'import vault_lib' not in s:
        s = s.replace(
            'from fastapi import FastAPI, HTTPException',
            'import sys\nimport json\nsys.path.insert(0, "/app/obsidian")\nimport vault_lib\n\nfrom fastapi import FastAPI, HTTPException'
        )
    if 'AGENT_NAME' not in s:
        s = s.replace('MAX_HISTORY     = 20', 'MAX_HISTORY     = 20\nAGENT_NAME      = "mark"')
    if 'ANTHROPIC_TOOLS' not in s:
        s = s.replace('# ── State', 'ANTHROPIC_TOOLS = vault_lib.get_tools_anthropic(AGENT_NAME)\n\n\n# ── State')
    if 'tool_use' not in s:
        old = '''async def _call_llm(msgs: list[dict], system: str) -> tuple[str, int, int]:
    """Abstração multi-provider. Retorna (reply, input_tokens, output_tokens)."""
    if AGENT_PROVIDER == "anthropic":
        r = await _client.messages.create(
            model=AGENT_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system,
            messages=msgs,
        )
        return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens
    else:  # openai
        r = await _client.chat.completions.create(
            model=AGENT_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            messages=[{"role": "system", "content": system}] + msgs,
        )
        u = r.usage
        return r.choices[0].message.content, u.prompt_tokens, u.completion_tokens'''
        new = '''async def _dispatch_tool(name: str, inp: dict) -> str:
    """Vault tools — read-only. Nunca escreve no vault."""
    if name == "search_vault":
        return str(vault_lib.search_vault(AGENT_NAME, inp.get("query", "")))
    if name == "read_vault_note":
        return str(vault_lib.read_vault_note(AGENT_NAME, inp.get("path", "")))
    return f"[ERRO] Tool desconhecida: {name}"


async def _call_llm(msgs: list[dict], system: str) -> tuple[str, int, int]:
    """Anthropic tool-use loop para vault. Retorna (reply, input_tokens, output_tokens)."""
    total_in = total_out = 0
    if AGENT_PROVIDER == "anthropic":
        while True:
            r = await _client.messages.create(
                model=AGENT_MODEL, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
                system=system, messages=msgs, tools=ANTHROPIC_TOOLS,
            )
            total_in += r.usage.input_tokens
            total_out += r.usage.output_tokens
            if r.stop_reason == "tool_use":
                msgs.append({"role": "assistant", "content": r.content})
                results = []
                for block in r.content:
                    if block.type == "tool_use":
                        result = await _dispatch_tool(block.name, block.input)
                        results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
                msgs.append({"role": "user", "content": results})
            else:
                text = next((b.text for b in r.content if hasattr(b, "text")), "")
                return text, total_in, total_out
    else:
        r = await _client.chat.completions.create(
            model=AGENT_MODEL, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
            messages=[{"role": "system", "content": system}] + msgs,
        )
        u = r.usage
        return r.choices[0].message.content, u.prompt_tokens, u.completion_tokens'''
        s = s.replace(old, new)
    open(p, 'w').write(s)
    print(f'mark:  OK search_vault={("search_vault" in s)} tool_use={("tool_use" in s)} import={("vault_lib" in s)}')

patch_james()
patch_rick()
patch_regi()
patch_mark()
print('\nTodos patcheados. Proximo: docker compose build + up.')
