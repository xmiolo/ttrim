# token-trim

Interceptador de inputs para o **Claude CLI** que comprime prompts e arquivos antes de enviar ao modelo — reduzindo custo de tokens em 30–85% dependendo do tipo de arquivo.

---

## Instalação

```bash
git clone https://github.com/xmiolo/ttrim
cd token-trim
chmod +x install.sh
./install.sh
source ~/.zshrc   # ou ~/.bashrc
```

O installer faz automaticamente:
- Instala as dependências Python (`toon-python`, `tiktoken`)
- Copia os arquivos para `~/.token-trim/`
- Instala o binário `ttrim` em `~/.local/bin/`
- Adiciona `TOKEN_TRIM_HOME` ao seu shell rc
- Garante `~/.local/bin` no PATH
- Instala o slash command `/toon` no Claude Code (se disponível)

---

## Uso

```bash
# Prompt simples (comprime polidez e verbosidade)
ttrim "por favor me explica como funciona esse service"

# Com arquivo Java
ttrim "review dessa implementação" --file OrderService.java

# Com múltiplos arquivos (tipos mistos)
ttrim "tem acoplamento aqui?" --file OrderService.java --file PaymentService.java

# Com arquivo Markdown (bug report, US, ADR)
ttrim "aplica esse fix" --file Invalid_fix.md

# Com diff do git
ttrim "review do que mudei" --diff

# Com arquivo de patch específico
ttrim "analisa esse diff" --diff meu.patch

# Ver tokens economizados sem chamar o claude
ttrim_DRY_RUN=1 ttrim "review" --file OrderService.java --stats

# Sem conversão (passa direto ao claude)
ttrim --no-toon "prompt literal"
```

### Flags

| Flag | Descrição |
|---|---|
| `--file / -f` | Arquivo a converter (pode repetir para múltiplos) |
| `--diff / -d` | Git diff do HEAD (ou caminho para arquivo `.patch`) |
| `--stats / -s` | Exibe tokens original vs comprimido |
| `--no-toon` | Passa direto ao claude sem conversão |
| `--help / -h` | Ajuda |

### Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `ttrim_DEBUG=1` | Exibe o output comprimido antes de enviar |
| `ttrim_DRY_RUN=1` | Não chama o claude (só mostra o output) |
| `TOKEN_TRIM_HOME` | Caminho alternativo para a instalação |

---

## Como funciona por tipo de arquivo

### `.json` → TOON (Token-Oriented Objettrim Notation)

Usa a [lib oficial toon-python](https://github.com/toon-format/toon-python) para converter dados estruturados para o formato TOON, que combina indentação YAML com layout tabular CSV.

**Economia típica: 40–60%**

```
# JSON formatado (244 tokens)
{
  "produtos": [
    { "id": 1001, "nome": "Dipirona 500mg", "preco": 12.90 },
    { "id": 1002, "nome": "Vitamina C 1g",  "preco": 24.50 }
  ]
}

# TOON (100 tokens)
produtos[2]{id,nome,preco}:
  1001,Dipirona 500mg,12.9
  1002,Vitamina C 1g,24.5
```

Arrays uniformes de objetos são o caso ideal — o schema é declarado uma vez no header e os valores ficam em linhas CSV compattrimas.

### `.java` / `.ts` / `.tsx` → extração estrutural

Arquivos de código não são dados — TOON não se aplica diretamente. O algoritmo extrai a estrutura relevante: package, imports agrupados por raiz, classes/interfaces com seus métodos e injeções de dependência.

**Economia típica: 55–65%**

```
# Java original → java_struttrimure[OrderService.java]
  pkg: com.panvel.pdv.service
  imports: {com,org}
  type: public class OrderService
    fn: public Order findById(Long id)
    fn: public void save(Order order)

# TypeScript/Angular → ts_struttrimure[produttrim.service.ts]
  type[@Injettrimable]: export class ProduttrimService
    injettrim: {http:HttpClient, cache:CacheService}
    fn: public getAll(): Observable<Produttrim[]>
```

### `.md` / `.markdown` → compressão estrutural

Documentos Markdown técnicos (bug reports, user stories, ADRs, notas de fix) contêm muito conteúdo de baixo valor para uma IA: checklists de QA, seções de backlog, notas defensivas repetitivas, metadados decorativos.

O algoritmo passa linha a linha e aplica quatro filtros em sequência:

```
                    ┌─────────────────────────┐
                    │    linha do arquivo .md  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     é um cabeçalho?      │
                    └──┬─────────────────┬────┘
                    sim│                 │não
                       ▼                 │
          ┌────────────────────┐         │
          │ seção de baixo     │         │
          │    valor?          │         │
          └──┬──────────────┬──┘         │
          sim│              │não         │
             ▼              │            ▼
    ╔════════════════╗      │  ┌─────────────────────────┐
    ║ DESCARTA seção ║      │  │    é linha decorativa?   │
    ║ inteira        ║      │  │  > **Fonte:**, ---, Next │
    ╚════════════════╝      │  └──┬──────────────────┬───┘
  verificação, fora         │  sim│                  │não
  de escopo, checklist...   │     ▼                  │
                            │  ╔══════════════╗      │
                            │  ║ DESCARTA     ║      │
                            │  ║ linha        ║      │
                            │  ╚══════════════╝      │
                            │                        ▼
                            │  ┌─────────────────────────┐
                            │  │  começa com "Por que X:" │
                            │  │  bloco explicativo       │
                            │  └──┬──────────────────┬───┘
                            │  sim│                  │não
                            │     ▼                  │
                            │  ╔══════════════╗      │
                            │  ║ DESCARTA     ║      │
                            │  ║ bloco        ║      │
                            │  ╚══════════════╝      │
                            │                        ▼
                            │  ┌─────────────────────────┐
                            │  │ bullet "não tocar em X"? │
                            │  │ "não cabe neste PR"...   │
                            │  └──┬──────────────────┬───┘
                            │  sim│                  │não
                            │     ▼                  │
                            │  ╔══════════════╗      │
                            │  ║ DESCARTA     ║      │
                            │  ║ linha        ║      │
                            │  ╚══════════════╝      │
                            │                        │
                            └──────────┬─────────────┘
                                       ▼
                    ┌─────────────────────────────────┐
                    │         ✓ MANTÉM a linha         │
                    └─────────────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────┐
                    │    MD comprimido (~57% menos)    │
                    │  zero API · zero rede · só regex │
                    └─────────────────────────────────┘
```




**Economia típica: 50–60% — zero dependências, zero rede, zero API key**

```
# Seções removidas por título:
  Verificação / Fora de escopo / Checklist / Manual HML / How to test

# Linhas removidas individualmente:
  > **Fonte:** ...      (metadado decorativo)
  > **Data:** ...       (metadado decorativo)
  ---                   (separador visual)
  → Next: /comando      (navegação)

# Blocos "Por que X:" removidos:
  Explicações do root cause que repetem o que já foi dito de forma concisa

# Bullets defensivos removidos:
  - **calculaExpiration()** já está protegido... não precisa ser tocado
  - **Sem refattrimor:** não criar V2, não tocar toggle...
```

O que **nunca é removido**: root cause, code blocks, file paths, line numbers, restrições críticas.

**Exemplo real** (`Invalid_fix.md`, 2059 tokens → 888 tokens, economia de 57%):

```bash
ttrim_DRY_RUN=1 ttrim "aplica esse fix" --file Invalid_fix.md --stats

# TOKEN STATS
# original  : 2059 tokens
# comprimido:  888 tokens
# economia  : 1171 tokens (56.8%)
```

### Prompt → limpeza de verbosidade

Remove polidez e verbosidade humana desnecessária do texto do prompt antes de enviar. Não é TOON — é uma limpeza independente de linguagem natural.

```
# Antes
"por favor poderia me ajudar a entender como funciona essa implementação do repositório"

# Depois
"entender como funciona essa impl do repo"
```

Abreviações aplicadas: `implementação → impl`, `configuração → config`, `repositório → repo`, `dependências → deps`.

### `git diff` → resumo compattrimo

```
diff_toon[2files]:
  file: src/OrderService.java
    removed[3]: private void oldMethod() { | // removido
    added[4]:   public Order findByCode(String code) { | return repo.findByCode(code);
  file: src/PaymentService.java
    added[2]:   public void refund(Long orderId) {
```

---

## Comparativo de economia por tipo

| Tipo | Método | Economia típica | Dependência |
|---|---|---|---|
| `.json` | TOON via lib oficial | 40–60% | `toon-python` |
| `.java` / `.ts` | Extração estrutural | 55–65% | nenhuma |
| `.md` | Compressão estrutural | 50–60% | nenhuma |
| prompt | Limpeza de verbosidade | 10–30% | nenhuma |
| `git diff` | Resumo compattrimo | 60–75% | nenhuma |

---

## Estrutura do projeto

```
token-trim/
├── bin/
│   └── ttrim                    # comando principal (shell wrapper)
├── src/
│   ├── converter.py          # lógica de conversão: TOON, extração Java/TS, diff
│   └── md_compress.py        # compressão estrutural de Markdown (offline)
├── tests/
│   └── test_converter.py     # 28 testes unitários
├── claude-commands/
│   └── toon.md               # slash command /toon para Claude Code
├── install.sh                # instalador com auto-detecção de shell
└── README.md
```

---

## O que é TOON?

**Token-Oriented Objettrim Notation** — formato de serialização compattrimo projetado para LLMs. Combina indentação YAML para objetos aninhados com layout tabular CSV para arrays uniformes.

LLMLingua — Microsoft Research — [LLMLingua Series | Effectively Deliver Information to LLMs via Prompt Compression](https://llmlingua.com/)
LLMLingua paper (arXiv) - [Compressing Prompts for Accelerated Inference of Large Language Models](https://arxiv.org/abs/2310.05736)
Spec oficial: [github.com/toon-format/toon](https://github.com/toon-format/toon)
Lib Python: [github.com/toon-format/toon-python](https://github.com/toon-format/toon-python)
Artigo introdutório (pt-BR): [medium.com/@habbema](https://medium.com/@habbema/toon-o-novo-formato-de-dados-otimizado-para-llms-cbfed80e1e52)

---

## Testes

```bash
python3 tests/test_converter.py
```

---

## Desinstalar

```bash
~/.token-trim/uninstall.sh
```

---

## Roadmap

- [ ] Cache de arquivos já convertidos (hash-based)
- [ ] Modo `--context` — extrai só métodos relevantes ao prompt via grep semântico
- [ ] Suporte a múltiplos arquivos via glob (`--file "src/**/*.java"`)
