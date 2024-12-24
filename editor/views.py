import os
import subprocess
import google.generativeai as genai
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import tempfile
import logging

# Configuration du logging
logger = logging.getLogger(__name__)

# Configuration de l'API Gemini
genai.configure(api_key='')
model = genai.GenerativeModel('gemini-1.5-flash')

def index(request):
    return render(request, 'editor/index.html')

@csrf_exempt
def execute_code(request):
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request body: {request.body}")
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        code = request.POST.get('code')
        language = request.POST.get('language')
        
        logger.info(f"Language: {language}")
        logger.debug(f"Code: {code}")
        
        if not code or not language:
            return JsonResponse({'error': 'Code and language are required'}, status=400)

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
        elif language == 'python':
            result = execute_python_code(code)
        else:
            result['errors'] = 'Langage non pris en charge.'

        # Analyse du code avec Gemini seulement si il y a des erreurs
        try:
            if result['errors']:
                result['suggestions'] = get_code_suggestions(code, result['errors'], language)
            result['improvements'] = get_code_improvements(code, language)
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            result['suggestions'] = "Erreur lors de l'analyse du code."
            result['improvements'] = "Erreur lors de l'analyse des améliorations."

        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

def execute_c_code(code):
    result = {'output': '', 'errors': ''}
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.c', delete=False) as f:
            f.write(code.encode())
            temp_path = f.name

        compile_process = subprocess.run(['gcc', temp_path, '-o', temp_path + '.out'],
                                      capture_output=True, text=True)

        if compile_process.returncode == 0:
            run_process = subprocess.run([temp_path + '.out'],
                                      capture_output=True, text=True, timeout=5)
            result['output'] = run_process.stdout
            result['errors'] = run_process.stderr
        else:
            result['errors'] = compile_process.stderr

    except subprocess.TimeoutExpired:
        result['errors'] = 'Timeout: Le programme a pris trop de temps à s\'exécuter'
    except Exception as e:
        logger.error(f"C code execution error: {str(e)}", exc_info=True)
        result['errors'] = str(e)
    finally:
        if temp_path:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(temp_path + '.out'):
                    os.remove(temp_path + '.out')
            except Exception as e:
                logger.error(f"Error cleaning up C files: {str(e)}")

    return result

def execute_java_code(code):
    result = {'output': '', 'errors': ''}
    temp_path = None
    try:
        class_name = "Main"
        with tempfile.NamedTemporaryFile(suffix='.java', delete=False) as f:
            f.write(code.encode())
            temp_path = f.name

        compile_process = subprocess.run(['javac', temp_path],
                                      capture_output=True, text=True)

        if compile_process.returncode == 0:
            run_process = subprocess.run(['java', '-cp', os.path.dirname(temp_path), class_name],
                                      capture_output=True, text=True, timeout=5)
            result['output'] = run_process.stdout
            result['errors'] = run_process.stderr
        else:
            result['errors'] = compile_process.stderr

    except subprocess.TimeoutExpired:
        result['errors'] = 'Timeout: Le programme a pris trop de temps à s\'exécuter'
    except Exception as e:
        logger.error(f"Java code execution error: {str(e)}", exc_info=True)
        result['errors'] = str(e)
    finally:
        if temp_path:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(os.path.join(os.path.dirname(temp_path), class_name + '.class')):
                    os.remove(os.path.join(os.path.dirname(temp_path), class_name + '.class'))
            except Exception as e:
                logger.error(f"Error cleaning up Java files: {str(e)}")

    return result

def execute_python_code(code):
    result = {'output': '', 'errors': ''}
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(code.encode())
            temp_path = f.name

        run_process = subprocess.run(['python', temp_path],
                                  capture_output=True, text=True, timeout=5)
        result['output'] = run_process.stdout
        result['errors'] = run_process.stderr

    except subprocess.TimeoutExpired:
        result['errors'] = 'Timeout: Le programme a pris trop de temps à s\'exécuter'
    except Exception as e:
        logger.error(f"Python code execution error: {str(e)}", exc_info=True)
        result['errors'] = str(e)
    finally:
        if temp_path:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                logger.error(f"Error cleaning up Python file: {str(e)}")

    return result

def get_code_suggestions(code, errors, language):
    try:
        prompt = f"""Voici un code en {language}:
        {code}
        
        On a cette erreur
        {errors}
        
        Montre d'où est le problème et donne des solutions. Donne des réponses courtes ne dépassant pas les 30 mots."""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error getting code suggestions: {str(e)}")
        return "Erreur lors de l'analyse du code"

def get_code_improvements(code, language):
    try:
        prompt = f"""Revois ce code en {language} et donne des points à améliorer:
        {code}
        
        Focus surtout :
        - sur les bonnes pratiques
        - ce qu'on peut améliorer dessus
        - s'il est préférable d'utiliser des fonctions
        
        Donne directement le code d'amélioration. Le message ne doit pas dépasser 30 mots."""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error getting code improvements: {str(e)}")
        return "Erreur lors de l'analyse des améliorations"