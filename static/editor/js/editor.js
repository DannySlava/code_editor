let editor = CodeMirror.fromTextArea(document.getElementById("code"), {
    lineNumbers: true,
    theme: "monokai",
    mode: "text/x-csrc",
    indentUnit: 4,
    autoCloseBrackets: true,
    matchBrackets: true,
    lineWrapping: true,
    tabSize: 4,
    styleActiveLine: true,
    extraKeys: {
        "Ctrl-Enter": function(cm) {
            document.getElementById('runBtn').click();
        }
    }
});

// Ajout d'un exemple de code par défaut
editor.setValue('// Écrivez votre code ici\n');

document.getElementById('language').addEventListener('change', function(e) {
    let mode = 'text/x-csrc';
    let defaultCode = '// Codez\n';
    
    if (e.target.value === 'java') {
        mode = 'text/x-java';
        defaultCode = 'public class Main {\n    public static void main(String[] args) {\n        // Écrivez votre code ici\n    }\n}';
    } else if (e.target.value === 'python') {
        mode = 'text/x-python';
        defaultCode = '# Codez\n';
    }
    
    editor.setOption('mode', mode);
    if (editor.getValue().trim() === '') {
        editor.setValue(defaultCode);
    }
});

document.getElementById('runBtn').addEventListener('click', function() {
    const button = this;
    const originalContent = button.innerHTML;
    const code = editor.getValue();
    const language = document.getElementById('language').value;
    
    // Animation de chargement
    button.innerHTML = '<div class="loading"></div> Exécution...';
    button.disabled = true;
    
    document.getElementById('output').textContent = 'Exécution en cours...';
    document.getElementById('errors').textContent = '';
    document.getElementById('improvements').textContent = '';

    fetch('/execute/', {
        method: 'POST',
        body: new URLSearchParams({
            'code': code,
            'language': language
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('output').textContent = data.output || 'Pas de sortie';
        document.getElementById('errors').innerHTML = data.errors ? 
            `Erreurs:<br>${data.errors}<br><br>Suggestions:<br>${data.suggestions}` : 
            'Aucune erreur';
        document.getElementById('improvements').innerHTML = data.improvements || 'Pas de suggestions';
    })
    .catch(error => {
        document.getElementById('output').textContent = 'Erreur lors de l\'exécution';
        document.getElementById('errors').textContent = error.toString();
    })
    .finally(() => {
        button.innerHTML = originalContent;
        button.disabled = false;
    });
});

// Raccourci clavier Ctrl+Enter pour l'éxécution
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        document.getElementById('runBtn').click();
    }
});