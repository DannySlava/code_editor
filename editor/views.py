# editor/views.py

import os
import subprocess
import google.generativeai as genai
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import tempfile

# Configuration de l'API Gemini
genai.configure(api_key='AIzaSyDrczwEYVVy61rpwG_WjoSArclVWuAShhQ')
model = genai.GenerativeModel('gemini-1.5-flash')

def index(request):
    return render(request, 'editor/index.html')

@csrf_exempt
def execute_code(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        language = request.POST.get('language')
        
        result = {
            'output': '',
            'errors': '',
            'suggestions': '',
            'improvements': ''
        }

        # Exécution du code
        if language == 'c':
            result = execute_c_code(code)
        elif language == 'java':
            result = execute_java_code(code)

        # Analyse du code avec Gemini
        if result['errors']:
            result['suggestions'] = get_code_suggestions(code, result['errors'], language)
        result['improvements'] = get_code_improvements(code, language)

        return JsonResponse(result)

# def execute_c_code(code):
#     result = {'output': '', 'errors': ''}
#     try:
#         with tempfile.NamedTemporaryFile(suffix='.c', delete=False) as f:
#             f.write(code.encode())
#             temp_path = f.name


#         compile_process = subprocess.run(['gcc', temp_path, '-o', temp_path + '.out'],
#                                       capture_output=True, text=True)
        
#         if compile_process.returncode == 0:
#             # Exécution
#             run_process = subprocess.run([temp_path + '.out'],
#                                       capture_output=True, text=True, timeout=5)
#             result['output'] = run_process.stdout
#             result['errors'] = run_process.stderr
#         else:
#             result['errors'] = compile_process.stderr

#     except Exception as e:
#         result['errors'] = str(e)
#     finally:

#         if os.path.exists(temp_path):
#             os.remove(temp_path)
#         if os.path.exists(temp_path + '.out'):
#             os.remove(temp_path + '.out')
    
#     return result

def execute_java_code(code):
    result = {'output': '', 'errors': ''}
    try:
        # Extraction du nom de la classe
        class_name = "Main"  
        with tempfile.NamedTemporaryFile(suffix='.java', delete=False) as f:
            f.write(code.encode())
            temp_path = f.name

        # Compilation
        compile_process = subprocess.run(['javac', temp_path],
                                      capture_output=True, text=True)
        
        if compile_process.returncode == 0:

            run_process = subprocess.run(['java', '-cp', os.path.dirname(temp_path), class_name],
                                      capture_output=True, text=True, timeout=5)
            result['output'] = run_process.stdout
            result['errors'] = run_process.stderr
        else:
            result['errors'] = compile_process.stderr

    except Exception as e:
        result['errors'] = str(e)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(os.path.dirname(temp_path) + '/' + class_name + '.class'):
            os.remove(os.path.dirname(temp_path) + '/' + class_name + '.class')
    
    return result


def execute_python_code(code):
    result = {'output': '', 'errors': ''}
    try:
        # Créer un fichier temporaire pour le code Python
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(code.encode())
            temp_path = f.name

        # Exécuter le script Python
        run_process = subprocess.run(['python', temp_path],
                                      capture_output=True, text=True, timeout=5)
        result['output'] = run_process.stdout
        result['errors'] = run_process.stderr

    except Exception as e:
        result['errors'] = str(e)
    finally:
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return result


def get_code_suggestions(code, errors, language):
    prompt = f"""Voici un code en {language}:
    {code}
    
    On a cette erreur
    {errors}
    
    Montre d'où est le problème et donne des solutions. Donne des reponses courtes ne dépassant pas les 30 mots."""
    
    response = model.generate_content(prompt)
    return response.text

def get_code_improvements(code, language):
    prompt = f"""Revois ce code en {language} et donne des points à améliorer:
    {code}
    
    Focus surtout :
    - sur les bonnes pratiques
    - ce qu'on peut améliorer dessus
    - s'il est préférable d'utiliser des fonctions
    
    Donne direct le code d'amélioration. Le message ne doit pas dépasser 30 mots."""
    
    response = model.generate_content(prompt)
    return response.text