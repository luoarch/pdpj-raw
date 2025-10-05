#!/usr/bin/env python3
"""
Script para validar todas as variáveis de ambiente necessárias para o projeto PDPJ.

Este script analisa todo o código do projeto e identifica:
1. Todas as variáveis de ambiente definidas no config.py
2. Todas as variáveis utilizadas no código
3. Variáveis que estão faltando no .env
4. Variáveis que estão no .env mas não são utilizadas
5. Sugestões de configuração baseadas no ambiente
"""

import os
import re
from pathlib import Path
from typing import Dict, Set, List, Tuple
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

class EnvironmentValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.app_dir = self.project_root / "app"
        self.env_file = self.project_root / ".env"
        self.env_example_file = self.project_root / "env.example"
        
        # Variáveis encontradas no código
        self.variables_in_code: Set[str] = set()
        # Variáveis definidas no config.py
        self.variables_in_config: Set[str] = set()
        # Variáveis no .env
        self.variables_in_env: Set[str] = set()
        # Variáveis no env.example
        self.variables_in_example: Set[str] = set()
        
    def extract_env_variables_from_file(self, file_path: Path) -> Set[str]:
        """Extrai variáveis de ambiente de um arquivo Python."""
        variables = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Padrões para encontrar variáveis de ambiente
            patterns = [
                r'os\.getenv\(["\']([^"\']+)["\']',  # os.getenv("VAR")
                r'os\.environ\[["\']([^"\']+)["\']',  # os.environ["VAR"]
                r'os\.environ\.get\(["\']([^"\']+)["\']',  # os.environ.get("VAR")
                r'Field\([^)]*env=["\']([^"\']+)["\']',  # Field(env="VAR")
                r'Field\([^)]*env_file=["\']([^"\']+)["\']',  # Field(env_file="VAR")
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                variables.update(matches)
                
        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")
            
        return variables
    
    def extract_config_fields(self, file_path: Path) -> Set[str]:
        """Extrai campos de configuração do config.py."""
        variables = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Encontrar definições de Field com env
            pattern = r'(\w+):\s*[^=]*=\s*Field\([^)]*env=["\']([^"\']+)["\']'
            matches = re.findall(pattern, content)
            
            for field_name, env_var in matches:
                variables.add(env_var)
                
            # Encontrar definições de Field sem env explícito (usa o nome do campo)
            pattern = r'(\w+):\s*[^=]*=\s*Field\('
            matches = re.findall(pattern, content)
            
            for field_name in matches:
                # Converter snake_case para UPPER_CASE
                env_var = field_name.upper()
                variables.add(env_var)
                
        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")
            
        return variables
    
    def load_env_file(self, file_path: Path) -> Set[str]:
        """Carrega variáveis de um arquivo .env."""
        variables = set()
        
        if not file_path.exists():
            return variables
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        var_name = line.split('=')[0].strip()
                        variables.add(var_name)
        except Exception as e:
            print(f"Erro ao carregar {file_path}: {e}")
            
        return variables
    
    def scan_project(self):
        """Escaneia todo o projeto em busca de variáveis de ambiente."""
        print("🔍 Escaneando projeto em busca de variáveis de ambiente...")
        
        # Escanear todos os arquivos Python
        for py_file in self.app_dir.rglob("*.py"):
            if py_file.name == "__pycache__":
                continue
                
            file_vars = self.extract_env_variables_from_file(py_file)
            self.variables_in_code.update(file_vars)
            
            # Extrair campos do config.py especificamente
            if py_file.name == "config.py":
                config_vars = self.extract_config_fields(py_file)
                self.variables_in_config.update(config_vars)
        
        # Carregar arquivos .env
        self.variables_in_env = self.load_env_file(self.env_file)
        self.variables_in_example = self.load_env_file(self.env_example_file)
        
        print(f"✅ Encontradas {len(self.variables_in_code)} variáveis no código")
        print(f"✅ Encontradas {len(self.variables_in_config)} variáveis no config.py")
        print(f"✅ Encontradas {len(self.variables_in_env)} variáveis no .env")
        print(f"✅ Encontradas {len(self.variables_in_example)} variáveis no env.example")
    
    def analyze_missing_variables(self) -> Dict[str, List[str]]:
        """Analisa variáveis que estão faltando."""
        analysis = {
            "missing_in_env": [],
            "missing_in_example": [],
            "unused_in_env": [],
            "unused_in_example": [],
            "critical_missing": [],
            "optional_missing": []
        }
        
        # Variáveis críticas que devem estar no .env
        critical_vars = {
            "DATABASE_URL", "REDIS_URL", "PDPJ_API_TOKEN", "PDPJ_API_BASE_URL",
            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET_NAME"
        }
        
        # Variáveis opcionais mas importantes
        optional_vars = {
            "SECRET_KEY", "SENTRY_DSN", "ENVIRONMENT", "DEBUG", "LOG_LEVEL"
        }
        
        # Verificar variáveis faltando no .env
        all_required = self.variables_in_config | self.variables_in_code
        for var in all_required:
            if var not in self.variables_in_env:
                if var in critical_vars:
                    analysis["critical_missing"].append(var)
                elif var in optional_vars:
                    analysis["optional_missing"].append(var)
                else:
                    analysis["missing_in_env"].append(var)
        
        # Verificar variáveis faltando no env.example
        for var in all_required:
            if var not in self.variables_in_example:
                analysis["missing_in_example"].append(var)
        
        # Verificar variáveis não utilizadas
        for var in self.variables_in_env:
            if var not in all_required and var not in {"# Configurações"}:
                analysis["unused_in_env"].append(var)
        
        for var in self.variables_in_example:
            if var not in all_required and var not in {"# Configurações"}:
                analysis["unused_in_example"].append(var)
        
        return analysis
    
    def generate_recommendations(self, analysis: Dict[str, List[str]]) -> List[str]:
        """Gera recomendações baseadas na análise."""
        recommendations = []
        
        if analysis["critical_missing"]:
            recommendations.append("🚨 CRÍTICO: Adicione as seguintes variáveis ao .env:")
            for var in analysis["critical_missing"]:
                recommendations.append(f"   - {var}")
        
        if analysis["optional_missing"]:
            recommendations.append("⚠️ IMPORTANTE: Considere adicionar as seguintes variáveis:")
            for var in analysis["optional_missing"]:
                recommendations.append(f"   - {var}")
        
        if analysis["missing_in_env"]:
            recommendations.append("ℹ️ SUGESTÃO: Adicione as seguintes variáveis ao .env:")
            for var in analysis["missing_in_env"]:
                recommendations.append(f"   - {var}")
        
        if analysis["missing_in_example"]:
            recommendations.append("📝 DOCUMENTAÇÃO: Adicione as seguintes variáveis ao env.example:")
            for var in analysis["missing_in_example"]:
                recommendations.append(f"   - {var}")
        
        if analysis["unused_in_env"]:
            recommendations.append("🧹 LIMPEZA: Considere remover variáveis não utilizadas do .env:")
            for var in analysis["unused_in_env"]:
                recommendations.append(f"   - {var}")
        
        return recommendations
    
    def print_analysis(self):
        """Imprime análise completa das variáveis de ambiente."""
        print("\n" + "="*80)
        print("📊 ANÁLISE COMPLETA DAS VARIÁVEIS DE AMBIENTE")
        print("="*80)
        
        # Escanear projeto
        self.scan_project()
        
        # Analisar variáveis faltando
        analysis = self.analyze_missing_variables()
        
        # Imprimir resumo
        print(f"\n📈 RESUMO:")
        print(f"   • Variáveis no código: {len(self.variables_in_code)}")
        print(f"   • Variáveis no config.py: {len(self.variables_in_config)}")
        print(f"   • Variáveis no .env: {len(self.variables_in_env)}")
        print(f"   • Variáveis no env.example: {len(self.variables_in_example)}")
        
        # Imprimir análise detalhada
        print(f"\n🔍 ANÁLISE DETALHADA:")
        
        if analysis["critical_missing"]:
            print(f"\n🚨 VARIÁVEIS CRÍTICAS FALTANDO NO .ENV ({len(analysis['critical_missing'])}):")
            for var in analysis["critical_missing"]:
                print(f"   ❌ {var}")
        
        if analysis["optional_missing"]:
            print(f"\n⚠️ VARIÁVEIS IMPORTANTES FALTANDO NO .ENV ({len(analysis['optional_missing'])}):")
            for var in analysis["optional_missing"]:
                print(f"   ⚠️ {var}")
        
        if analysis["missing_in_env"]:
            print(f"\nℹ️ VARIÁVEIS FALTANDO NO .ENV ({len(analysis['missing_in_env'])}):")
            for var in analysis["missing_in_env"]:
                print(f"   ℹ️ {var}")
        
        if analysis["missing_in_example"]:
            print(f"\n📝 VARIÁVEIS FALTANDO NO ENV.EXAMPLE ({len(analysis['missing_in_example'])}):")
            for var in analysis["missing_in_example"]:
                print(f"   📝 {var}")
        
        if analysis["unused_in_env"]:
            print(f"\n🧹 VARIÁVEIS NÃO UTILIZADAS NO .ENV ({len(analysis['unused_in_env'])}):")
            for var in analysis["unused_in_env"]:
                print(f"   🧹 {var}")
        
        # Gerar recomendações
        recommendations = self.generate_recommendations(analysis)
        
        if recommendations:
            print(f"\n💡 RECOMENDAÇÕES:")
            for rec in recommendations:
                print(rec)
        
        # Status geral
        total_issues = (
            len(analysis["critical_missing"]) + 
            len(analysis["optional_missing"]) + 
            len(analysis["missing_in_env"]) +
            len(analysis["missing_in_example"])
        )
        
        print(f"\n🎯 STATUS GERAL:")
        if total_issues == 0:
            print("   ✅ EXCELENTE! Todas as variáveis estão configuradas corretamente!")
        elif len(analysis["critical_missing"]) == 0:
            print("   ⚠️ BOM! Algumas variáveis opcionais estão faltando, mas nada crítico.")
        else:
            print("   🚨 ATENÇÃO! Variáveis críticas estão faltando. Corrija antes de continuar.")
        
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   • Total de problemas: {total_issues}")
        print(f"   • Críticos: {len(analysis['critical_missing'])}")
        print(f"   • Importantes: {len(analysis['optional_missing'])}")
        print(f"   • Sugestões: {len(analysis['missing_in_env'])}")
        print(f"   • Documentação: {len(analysis['missing_in_example'])}")
        
        return analysis

def main():
    """Função principal."""
    print("🔧 VALIDADOR DE VARIÁVEIS DE AMBIENTE - PDPJ PROJECT")
    print("="*60)
    
    validator = EnvironmentValidator()
    analysis = validator.print_analysis()
    
    # Verificar se há problemas críticos
    if analysis["critical_missing"]:
        print(f"\n❌ FALHA: {len(analysis['critical_missing'])} variáveis críticas estão faltando!")
        return 1
    elif analysis["optional_missing"]:
        print(f"\n⚠️ AVISO: {len(analysis['optional_missing'])} variáveis importantes estão faltando.")
        return 0
    else:
        print(f"\n✅ SUCESSO: Todas as variáveis necessárias estão configuradas!")
        return 0

if __name__ == "__main__":
    exit(main())
