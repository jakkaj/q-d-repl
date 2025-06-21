ARG VARIANT=bookworm
FROM mcr.microsoft.com/vscode/devcontainers/base:${VARIANT}

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev python3-wheel python3-setuptools python3-venv \
    apt-transport-https \
    wget unzip xz-utils zip \
    git curl poppler-utils \
    gh chromium \
    libglib2.0-0 libpango-1.0-0 libpangoft2-1.0-0 \
    pipx && \
    apt-get clean && \    
    rm -rf /var/lib/apt/lists/*  



ARG CODEQL_VERSION=2.22.0         # check https://github.com/github/codeql-cli-binaries/releases :contentReference[oaicite:0]{index=0}
RUN set -eux; \    
    CODEQL_URL="https://github.com/github/codeql-cli-binaries/releases/download/v${CODEQL_VERSION}/codeql-linux64.zip"; \
    curl -fL "$CODEQL_URL" -o /tmp/codeql.zip; \
    unzip -q /tmp/codeql.zip -d /opt; \
    ln -sf /opt/codeql/codeql /usr/local/bin/codeql; \
    rm /tmp/codeql.zip; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*
 

USER vscode
WORKDIR /home/vscode
ENV CHROME_EXECUTABLE=/usr/bin/google-chrome

ENV PATH="/home/vscode/.local/bin:${PATH}"

RUN pipx install rust-just

# Add VS Code shell integration to .zshrc
RUN echo '\n# VS Code Shell Integration\nif [ -n "$VSCODE_SHELL_INTEGRATION" ]; then\n  source "$(code --locate-shell-integration-path zsh)"\nelse\n  # Fallback for when code command exists but we are not in a VS Code terminal\n  if command -v code >/dev/null && [ -z "$VSCODE_SHELL_INTEGRATION" ]; then\n    VSCODE_SHELL_INT_PATH=$(code --locate-shell-integration-path zsh 2>/dev/null)\n    if [ -n "$VSCODE_SHELL_INT_PATH" ]; then\n      source "$VSCODE_SHELL_INT_PATH"\n    fi\n  fi\nfi' >> /home/vscode/.zshrc

RUN mkdir -p /home/vscode/.zfunc && \
    chown -R vscode:vscode /home/vscode/.zfunc && \
    bash -c "just --completions zsh" > /home/vscode/.zfunc/_just && \
    chown vscode:vscode /home/vscode/.zfunc/_just && \
    echo 'fpath=(/home/vscode/.zfunc $fpath)' >> /home/vscode/.zshrc && \
    echo 'autoload -Uz compinit && compinit' >> /home/vscode/.zshrc

# Add Python alias
RUN echo "alias python=python3" >> /home/vscode/.zshrc

# Add smart_debugger commands to PATH
RUN echo '\n# Smart Debugger Commands\nexport PATH="/workspaces/substrate/smart_debugger:$PATH"' >> /home/vscode/.zshrc
