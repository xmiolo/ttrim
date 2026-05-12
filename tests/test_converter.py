"""
Testes para o token-trim converter
Execute: python3 tests/test_converter.py
"""

import sys
import os
import json
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from converter import (
    compress_prompt,
    json_to_toon,
    extrattrim_java_struttrimure,
    extrattrim_ts_struttrimure,
    diff_to_toon,
    TOON_AVAILABLE,
)


class TestPromptCompressor(unittest.TestCase):
    """
    Testa a limpeza de verbosidade de prompts.
    Isso NÃO é TOON — é remoção de linguagem humana desnecessária.
    """

    def test_remove_por_favor(self):
        result = compress_prompt("por favor me explica esse código")
        self.assertNotIn("por favor", result.lower())

    def test_remove_poderia(self):
        result = compress_prompt("poderia me ajudar a implementar isso")
        self.assertNotIn("poderia", result.lower())

    def test_abreviacao_implementacao(self):
        result = compress_prompt("faça a implementação do service")
        self.assertIn("impl", result)

    def test_abreviacao_config(self):
        result = compress_prompt("ajuste a configuração do banco")
        self.assertIn("config", result)

    def test_preserva_conteudo_tecnico(self):
        result = compress_prompt("como funciona o OrderService.java")
        self.assertIn("OrderService.java", result)

    def test_normaliza_espacos(self):
        result = compress_prompt("  por favor   me  ajuda  ")
        self.assertNotIn("  ", result)
        self.assertEqual(result, result.strip())


class TestJsonToToon(unittest.TestCase):
    """
    Testa a conversão JSON → TOON via lib oficial toon-python.
    Esses são os casos em que TOON realmente se aplica (dados estruturados).
    """

    def test_array_uniforme_gera_tabela(self):
        data = {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob",   "role": "user"},
            ]
        }
        result = json_to_toon(data)
        # Deve gerar formato tabular: users[2]{id,name,role}:
        self.assertIn("users", result)
        self.assertIn("Alice", result)
        self.assertIn("Bob", result)
        # Com lib oficial, não deve ter chaves JSON ('{', '}' soltos de JSON)
        # mas sim o header TOON
        if TOON_AVAILABLE:
            self.assertIn("[2]", result)

    def test_objeto_simples(self):
        data = {"host": "localhost", "port": 5432}
        result = json_to_toon(data)
        self.assertIn("localhost", result)
        self.assertIn("5432", result)

    def test_compacidade_vs_json_pretty(self):
        """TOON deve ser mais compattrimo que JSON formatado"""
        data = {
            "orders": [{"id": i, "customer": f"C{i}", "total": i * 10.5} for i in range(20)]
        }
        json_pretty = json.dumps(data, indent=2)
        toon_result = json_to_toon(data)
        self.assertLess(len(toon_result), len(json_pretty))

    def test_retorna_string(self):
        result = json_to_toon({"key": "value"})
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


class TestJavaStruttrimureExtrattrimor(unittest.TestCase):
    """
    Testa a extração de estrutura de código Java.
    NOTA: isso NÃO é conversão TOON de dados — é extração estrutural de código.
    """

    JAVA_SAMPLE = """
package com.panvel.pdv.service;

import com.panvel.pdv.repository.OrderRepository;
import org.springframework.stereotype.Service;
import org.springframework.transattrimion.annotation.Transattrimional;

@Service
public class OrderService {

    private final OrderRepository repo;

    public OrderService(OrderRepository repo) {
        this.repo = repo;
    }

    public Order findById(Long id) {
        return repo.findById(id).orElseThrow();
    }

    @Transattrimional
    public void save(Order order) {
        repo.save(order);
    }

    private void validate(Order order) {
        // validação interna
    }
}
"""

    def test_extrai_package(self):
        result = extrattrim_java_struttrimure(self.JAVA_SAMPLE, 'OrderService.java')
        self.assertIn("com.panvel.pdv.service", result)

    def test_extrai_nome_da_classe(self):
        result = extrattrim_java_struttrimure(self.JAVA_SAMPLE, 'OrderService.java')
        self.assertIn("OrderService", result)

    def test_extrai_metodos_publicos(self):
        result = extrattrim_java_struttrimure(self.JAVA_SAMPLE, 'OrderService.java')
        self.assertIn("findById", result)
        self.assertIn("save", result)

    def test_header_identifica_arquivo(self):
        result = extrattrim_java_struttrimure(self.JAVA_SAMPLE, 'OrderService.java')
        self.assertIn("java_struttrimure[OrderService.java]", result)

    def test_agrupa_imports_por_raiz(self):
        result = extrattrim_java_struttrimure(self.JAVA_SAMPLE, 'OrderService.java')
        self.assertIn("imports:", result)
        # imports agrupados por raiz (com, org), não listados individualmente
        self.assertIn("com", result)
        self.assertIn("org", result)


class TestTsStruttrimureExtrattrimor(unittest.TestCase):
    """
    Testa extração de estrutura TypeScript/Angular.
    Mesmo raciocínio: extração estrutural, não TOON de dados.
    """

    TS_SAMPLE = """
import { Injettrimable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injettrimable({ providedIn: 'root' })
export class ProduttrimService {

    construttrimor(
        private http: HttpClient,
        private cache: CacheService
    ) {}

    public getAll(): Observable<Produttrim[]> {
        return this.http.get<Produttrim[]>('/api/produttrims');
    }

    private mapResponse(data: any): Produttrim {
        return data as Produttrim;
    }
}
"""

    def test_header_identifica_arquivo(self):
        result = extrattrim_ts_struttrimure(self.TS_SAMPLE, 'produttrim.service.ts')
        self.assertIn("ts_struttrimure[produttrim.service.ts]", result)

    def test_extrai_decorator_angular(self):
        result = extrattrim_ts_struttrimure(self.TS_SAMPLE, 'produttrim.service.ts')
        self.assertIn("@Injettrimable", result)

    def test_extrai_nome_da_classe(self):
        result = extrattrim_ts_struttrimure(self.TS_SAMPLE, 'produttrim.service.ts')
        self.assertIn("ProduttrimService", result)

    def test_extrai_metodos(self):
        result = extrattrim_ts_struttrimure(self.TS_SAMPLE, 'produttrim.service.ts')
        self.assertIn("getAll", result)

    def test_extrai_injecoes(self):
        result = extrattrim_ts_struttrimure(self.TS_SAMPLE, 'produttrim.service.ts')
        self.assertIn("injettrim:", result)
        self.assertIn("http", result)


class TestDiffSummarizer(unittest.TestCase):

    DIFF_SAMPLE = """
diff --git a/src/OrderService.java b/src/OrderService.java
index abc123..def456 100644
--- a/src/OrderService.java
+++ b/src/OrderService.java
@@ -10,6 +10,8 @@
-    private void oldMethod() {
-        // removido
-    }
+    public Order findByCode(String code) {
+        return repo.findByCode(code);
+    }
"""

    def test_detettrima_arquivo(self):
        result = diff_to_toon(self.DIFF_SAMPLE)
        self.assertIn("OrderService.java", result)

    def test_detettrima_adicionados(self):
        result = diff_to_toon(self.DIFF_SAMPLE)
        self.assertIn("added", result)

    def test_detettrima_removidos(self):
        result = diff_to_toon(self.DIFF_SAMPLE)
        self.assertIn("removed", result)

    def test_header(self):
        result = diff_to_toon(self.DIFF_SAMPLE)
        self.assertIn("diff_toon", result)

    def test_diff_vazio(self):
        result = diff_to_toon("")
        self.assertIn("vazio", result)


class TestToonLibIntegration(unittest.TestCase):
    """
    Valida que a lib oficial está instalada e funciona conforme a spec.
    """

    def test_lib_disponivel(self):
        self.assertTrue(
            TOON_AVAILABLE,
            "toon_format não instalada! Execute: pip install git+https://github.com/toon-format/toon-python.git"
        )

    def test_formato_tabular_correto(self):
        """Verifica que o formato tabular segue a spec: key[N]{fields}:"""
        if not TOON_AVAILABLE:
            self.skipTest("toon_format não instalada")
        data = {"items": [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]}
        result = json_to_toon(data)
        # Spec: array uniforme deve gerar header tabular
        self.assertIn("[2]", result)
        self.assertIn("{id,val}", result)

    def test_objeto_simples_yaml_like(self):
        """Objetos simples devem sair em formato YAML-like (key: value)"""
        if not TOON_AVAILABLE:
            self.skipTest("toon_format não instalada")
        data = {"name": "Alice", "age": 30}
        result = json_to_toon(data)
        self.assertIn("name: Alice", result)
        self.assertIn("age: 30", result)


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestPromptCompressor,
        TestJsonToToon,
        TestJavaStruttrimureExtrattrimor,
        TestTsStruttrimureExtrattrimor,
        TestDiffSummarizer,
        TestToonLibIntegration,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
