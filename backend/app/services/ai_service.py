"""
AI Service for financial analysis and configuration assistance using OpenAI GPT-4
"""

import hashlib
import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.core.cache import get_cache
from app.core.config import settings
from app.schemas.ai import ExecutiveSummaryRequest

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered financial analysis"""

    def __init__(self):
        """Initialize OpenAI client from environment configuration."""
        self.provider = (getattr(settings, "AI_PROVIDER", "openai") or "openai").strip().lower()
        self.model = (getattr(settings, "AI_MODEL", "gpt-4o-mini") or "gpt-4o-mini").strip()
        self.timeout_seconds = max(5, int(getattr(settings, "AI_TIMEOUT_SECONDS", 30) or 30))
        self.max_retries = max(0, int(getattr(settings, "AI_MAX_RETRIES", 2) or 2))
        api_key = getattr(settings, "OPENAI_API_KEY", None)
        if self.provider != "openai":
            logger.warning(
                "Unsupported AI_PROVIDER configured. Only 'openai' is currently supported.",
                extra={"provider": self.provider},
            )
            self.client = None
        elif not api_key:
            logger.warning("OPENAI_API_KEY not configured. AI features will be disabled.")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                api_key=api_key,
                timeout=self.timeout_seconds,
                max_retries=self.max_retries,
            )

    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.client is not None

    async def analyze_financial_data(self, context: dict, question: str | None = None) -> dict:
        """
        Analyze financial data and provide insights

        Args:
            context: Dictionary with financial data (projects, costs, team, etc.)
            question: Optional specific question from user

        Returns:
            Dictionary with analysis and recommendations
        """
        if not self.is_available():
            return {
                "error": "AI service not configured. Please set OPENAI_API_KEY.",
                "success": False,
            }

        try:
            # Build prompt with context
            prompt = self._build_financial_prompt(context, question)

            # Call GPT-4
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un CFO experto y asesor financiero para agencias digitales.

Tu objetivo es analizar datos financieros y proporcionar:
1. Análisis claro y estructurado
2. Insights accionables
3. Recomendaciones específicas con números
4. Identificación de riesgos y oportunidades

Responde SIEMPRE en español.
Usa emojis para mejor legibilidad: 📊 📈 💰 ⚠️ ✅ 🎯 💡
Sé directo y específico con los números.
Prioriza recomendaciones por impacto esperado.""",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            analysis = response.choices[0].message.content

            return {
                "success": True,
                "analysis": analysis,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "estimated_cost": self._estimate_cost(response.usage),
                },
            }

        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {"error": f"Error al analizar: {str(e)}", "success": False}

    def _build_financial_prompt(self, context: dict, question: str | None = None) -> str:
        """Build prompt with financial context"""

        # Extract data from context
        total_costs = context.get("total_monthly_costs", 0)
        blended_rate = context.get("blended_cost_rate", 0)
        team_size = context.get("team_size", 0)
        total_hours = context.get("total_monthly_hours", 0)
        projects = context.get("projects", [])
        services = context.get("services", [])
        primary_currency = context.get("primary_currency", "USD")

        # Calculate project metrics
        total_revenue = sum(p.get("total_price", 0) for p in projects)
        won_projects = [p for p in projects if p.get("status") == "won"]
        lost_projects = [p for p in projects if p.get("status") == "lost"]
        avg_margin = (
            sum(p.get("margin_percentage", 0) for p in projects) / len(projects) if projects else 0
        )

        # Build context string
        context_str = f"""
CONTEXTO FINANCIERO DE LA AGENCIA:

📊 COSTOS OPERATIVOS:
- Costos fijos mensuales: ${total_costs:,.2f} {primary_currency}
- Blended Cost Rate (costo por hora): ${blended_rate:.2f}/hora
- Equipo: {team_size} personas
- Horas disponibles/mes: {total_hours} horas

💼 PROYECTOS ({len(projects)} total):
- Proyectos ganados: {len(won_projects)}
- Proyectos perdidos: {len(lost_projects)}
- Ingresos totales: ${total_revenue:,.2f}
- Margen promedio: {avg_margin:.1f}%

🛠️ SERVICIOS ({len(services)} servicios):
"""

        # Add top services
        for service in services[:5]:
            context_str += f"- {service.get('name')}: Margen objetivo {service.get('default_margin_target', 0) * 100:.0f}%\n"

        # Add recent projects summary
        if projects:
            context_str += "\n📈 PROYECTOS RECIENTES:\n"
            for i, project in enumerate(projects[:5], 1):
                status_emoji = (
                    "✅"
                    if project.get("status") == "won"
                    else "❌"
                    if project.get("status") == "lost"
                    else "⏳"
                )
                context_str += f"{i}. {status_emoji} {project.get('name')}: ${project.get('total_price', 0):,.2f}, Margen: {project.get('margin_percentage', 0):.1f}%\n"

        # Add user question or default analysis request
        if question:
            context_str += f"\n\n❓ PREGUNTA ESPECÍFICA:\n{question}"
        else:
            context_str += """

📋 ANÁLISIS REQUERIDO:
Por favor proporciona:

1. 📊 RESUMEN EJECUTIVO: Estado general de la salud financiera

2. 💡 INSIGHTS CLAVE: 3-5 observaciones importantes sobre los datos

3. ⚠️ RIESGOS IDENTIFICADOS: Qué problemas o alertas ves

4. 🎯 OPORTUNIDADES: Dónde hay potencial de mejora

5. 🚀 RECOMENDACIONES: 3-5 acciones concretas priorizadas por impacto esperado
   (incluye números y métricas específicas)
"""

        return context_str

    def _estimate_cost(self, usage) -> float:
        """Estimate cost of API call in USD"""
        # GPT-4 Turbo pricing
        input_cost = (usage.prompt_tokens / 1000) * 0.01
        output_cost = (usage.completion_tokens / 1000) * 0.03
        return round(input_cost + output_cost, 4)

    async def suggest_onboarding_data(
        self,
        industry: str,
        region: str = "US",
        currency: str = "USD",
        custom_context: str | None = None,
    ) -> dict:
        """
        Suggest onboarding data (team members, services, fixed costs) based on industry

        Args:
            industry: Industry type (e.g., 'Marketing Digital', 'Desarrollo Web')
            region: Region code (e.g., 'US', 'CO', 'MX')
            currency: Primary currency
            custom_context: Additional context about the business

        Returns:
            Dictionary with suggested roles, services, fixed costs, and confidence scores
        """
        if not self.is_available():
            return {
                "error": "AI service not configured. Please set OPENAI_API_KEY.",
                "success": False,
            }

        # Build cache key
        # Normalize industry name for cache key (lowercase, strip spaces)
        industry_normalized = industry.lower().strip()
        region_normalized = region.upper().strip()
        currency_normalized = currency.upper().strip()

        # If custom_context is provided, include a hash of it in the cache key
        # Otherwise, use a generic cache key for better hit rate
        if custom_context:
            # Hash custom_context to keep key manageable
            context_hash = hashlib.md5(custom_context.encode()).hexdigest()[:8]
            cache_key = f"ai_suggestion:{industry_normalized}:{region_normalized}:{currency_normalized}:ctx_{context_hash}"
        else:
            # Standard cache key without custom context (better hit rate)
            cache_key = (
                f"ai_suggestion:{industry_normalized}:{region_normalized}:{currency_normalized}"
            )

        # Check cache first (24 hours TTL for industry suggestions)
        cache = get_cache()
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(
                f"AI suggestion cache hit for industry={industry}, region={region}, currency={currency}"
            )
            return {
                "success": True,
                "data": cached_result,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost": 0.0,
                    "cached": True,
                },
            }

        try:
            # Build prompt for onboarding suggestions
            prompt = self._build_onboarding_prompt(industry, region, currency, custom_context)

            # Define JSON schema for structured output

            # Call GPT-4 with structured output
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto en configuración de agencias digitales y consultoría de operaciones.

Tu objetivo es sugerir una configuración inicial completa basada en la industria y región:
1. Roles típicos del equipo con salarios realistas para la región
2. Servicios comunes ofrecidos en esa industria
3. Costos fijos típicos (software, herramientas, etc.)

IMPORTANTE:
- Usa salarios realistas para la región especificada
- Incluye solo roles y servicios relevantes para la industria
- Los costos fijos deben ser típicos de la industria
- Proporciona confidence scores realistas (0.0 a 1.0)
- Responde SIEMPRE en formato JSON válido""",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=4000,
            )

            # Parse JSON response
            content = response.choices[0].message.content
            result = json.loads(content)

            return {
                "success": True,
                "data": result,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "estimated_cost": self._estimate_cost(response.usage),
                },
            }

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return {"error": "Error al parsear respuesta de IA", "success": False}
        except Exception as e:
            logger.error(f"Error in AI onboarding suggestion: {e}")
            return {"error": f"Error al generar sugerencias: {str(e)}", "success": False}

    async def parse_unstructured_data(self, text: str, document_type: str | None = None) -> dict:
        """
        Parse unstructured document data (payroll, expenses, etc.) into structured format

        Args:
            text: Text content from document (PDF, CSV, etc.)
            document_type: Type of document ('payroll', 'expenses', 'mixed')

        Returns:
            Dictionary with extracted team members, fixed costs, subscriptions, and confidence scores
        """
        if not self.is_available():
            return {
                "error": "AI service not configured. Please set OPENAI_API_KEY.",
                "success": False,
            }

        try:
            # Build prompt for document parsing
            prompt = self._build_document_parse_prompt(text, document_type)

            # Define JSON schema for structured output

            # Call GPT-4 with structured output
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto en extracción de datos financieros de documentos.

Tu objetivo es extraer información estructurada de documentos desordenados:
1. Identificar miembros del equipo y sus salarios
2. Identificar costos fijos recurrentes
3. Identificar suscripciones y servicios

IMPORTANTE:
- Extrae solo información clara y confiable
- Si hay ambigüedad, inclúyela en warnings
- Proporciona confidence scores realistas
- Normaliza montos a mensuales cuando sea necesario
- Responde SIEMPRE en formato JSON válido""",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower temperature for more accurate extraction
                max_tokens=4000,
            )

            # Parse JSON response
            content = response.choices[0].message.content
            result = json.loads(content)

            return {
                "success": True,
                "data": result,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "estimated_cost": self._estimate_cost(response.usage),
                },
            }

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return {"error": "Error al parsear respuesta de IA", "success": False}
        except Exception as e:
            logger.error(f"Error in AI document parsing: {e}")
            return {"error": f"Error al parsear documento: {str(e)}", "success": False}

    async def process_natural_language_command(
        self, command: str, context: dict | None = None
    ) -> dict:
        """
        Process natural language configuration commands

        Args:
            command: Natural language command (e.g., 'Añade un Senior Designer que gana 45k anuales')
            context: Current configuration context

        Returns:
            Dictionary with structured action data
        """
        if not self.is_available():
            return {
                "error": "AI service not configured. Please set OPENAI_API_KEY.",
                "success": False,
            }

        try:
            # Build prompt for command processing
            prompt = self._build_command_prompt(command, context)

            # Define JSON schema for structured output

            # Call GPT-4 with structured output
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un asistente experto en configuración de agencias digitales.

Tu objetivo es interpretar comandos en lenguaje natural y convertirlos en acciones estructuradas:
- add_team_member: Agregar miembro del equipo
- add_service: Agregar servicio
- add_fixed_cost: Agregar costo fijo
- update_team_member: Actualizar miembro del equipo
- delete_team_member: Eliminar miembro del equipo

IMPORTANTE:
- Interpreta el comando lo mejor posible
- Si hay ambigüedad, marca requires_confirmation como true
- Convierte salarios anuales a mensuales (dividir por 12)
- Proporciona confidence score realista
- Responde SIEMPRE en formato JSON válido""",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=2000,
            )

            # Parse JSON response
            content = response.choices[0].message.content
            result = json.loads(content)

            # Convert annual salary to monthly if provided
            if result.get("action_data", {}).get("salary_annual"):
                annual = result["action_data"]["salary_annual"]
                result["action_data"]["salary_monthly_brute"] = annual / 12
                result["action_data"].pop("salary_annual", None)

            return {
                "success": True,
                "data": result,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "estimated_cost": self._estimate_cost(response.usage),
                },
            }

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return {"error": "Error al parsear respuesta de IA", "success": False}
        except Exception as e:
            logger.error(f"Error in AI command processing: {e}")
            return {"error": f"Error al procesar comando: {str(e)}", "success": False}

    def _build_onboarding_prompt(
        self, industry: str, region: str, currency: str, custom_context: str | None
    ) -> str:
        """Build prompt for onboarding suggestions"""
        prompt = f"""Genera una configuración inicial completa para una agencia de {industry} en la región {region} con moneda {currency}.

INSTRUCCIONES:
1. Sugiere 3-8 roles típicos del equipo con salarios realistas para {region}
2. Sugiere 5-15 servicios comunes ofrecidos en {industry}
3. Sugiere 3-10 costos fijos típicos (software, herramientas, etc.)

CONTEXTO ADICIONAL:
"""
        if custom_context:
            prompt += f"{custom_context}\n"
        else:
            prompt += "Ninguno\n"

        prompt += """
FORMATO DE RESPUESTA (JSON):
{
  "suggested_roles": [
    {
      "name": "Nombre del miembro",
      "role": "Rol (ej: 'Senior Designer', 'SEO Specialist')",
      "salary_monthly_brute": 5000,
      "currency": "USD",
      "billable_hours_per_week": 32,
      "is_active": true
    }
  ],
  "suggested_services": [
    {
      "name": "Nombre del servicio",
      "description": "Descripción",
      "default_margin_target": 0.40,
      "pricing_type": "hourly",
      "is_active": true
    }
  ],
  "suggested_fixed_costs": [
    {
      "name": "Nombre del costo",
      "amount_monthly": 100,
      "currency": "USD",
      "category": "Software",
      "description": "Descripción"
    }
  ],
  "confidence_scores": {
    "roles": 0.85,
    "services": 0.90,
    "costs": 0.80
  },
  "reasoning": "Breve explicación de las sugerencias"
}
"""
        return prompt

    def _build_document_parse_prompt(self, text: str, document_type: str | None) -> str:
        """Build prompt for document parsing"""
        doc_type_context = ""
        if document_type:
            doc_type_context = f"\nTIPO DE DOCUMENTO: {document_type}\n"

        prompt = f"""Extrae información estructurada del siguiente documento:{doc_type_context}

DOCUMENTO:
{text}

INSTRUCCIONES:
1. Identifica miembros del equipo y sus salarios (convierte a mensual si es necesario)
2. Identifica costos fijos recurrentes
3. Identifica suscripciones y servicios
4. Si hay ambigüedad o datos incompletos, inclúyelos en warnings
5. Proporciona confidence scores realistas

FORMATO DE RESPUESTA (JSON):
{{
  "team_members": [...],
  "fixed_costs": [...],
  "subscriptions": [...],
  "confidence_scores": {{
    "team_members": 0.85,
    "fixed_costs": 0.80,
    "subscriptions": 0.75
  }},
  "warnings": ["Advertencias sobre datos ambiguos o incompletos"]
}}
"""
        return prompt

    def _build_command_prompt(self, command: str, context: dict | None) -> str:
        """Build prompt for natural language command processing"""
        context_str = ""
        if context:
            context_str = f"\nCONTEXTO ACTUAL:\n{json.dumps(context, indent=2)}\n"

        prompt = f"""Interpreta el siguiente comando en lenguaje natural y conviértelo en una acción estructurada:{context_str}

COMANDO: {command}

INSTRUCCIONES:
1. Identifica el tipo de acción (add_team_member, add_service, add_fixed_cost, etc.)
2. Extrae los datos relevantes del comando
3. Si hay ambigüedad, marca requires_confirmation como true
4. Convierte salarios anuales a mensuales (dividir por 12)
5. Proporciona confidence score realista

FORMATO DE RESPUESTA (JSON):
{{
  "action_type": "add_team_member",
  "action_data": {{
    "name": "Nombre (si se menciona)",
    "role": "Rol",
    "salary_monthly_brute": 3750,
    "currency": "USD",
    "billable_hours_per_week": 32
  }},
  "confidence": 0.90,
  "requires_confirmation": false,
  "reasoning": "Explicación de cómo se interpretó el comando"
}}
"""
        return prompt

    async def generate_executive_summary(self, request: ExecutiveSummaryRequest) -> dict[str, Any]:
        """
        Generar resumen ejecutivo para una cotización usando IA

        Args:
            request: ExecutiveSummaryRequest con datos del proyecto y servicios

        Returns:
            Dictionary con:
            {
                "success": bool,
                "summary": str,  # Resumen ejecutivo generado
                "usage": dict,    # Información de uso de la API
                "error": str      # Solo si success=False
            }
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "AI service not configured. Please set OPENAI_API_KEY in environment variables.",
            }

        try:
            # Construir prompt
            prompt = self._build_executive_summary_prompt(request)

            # Determinar idioma del sistema
            system_language = "español" if request.language == "es" else "english"

            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Eres un experto en redacción de propuestas comerciales y resúmenes ejecutivos para agencias digitales.

Tu objetivo es crear un resumen ejecutivo profesional, conciso y persuasivo que:
1. Presente el proyecto de manera clara y profesional
2. Destaque el valor de los servicios propuestos
3. Sea apropiado para presentar a ejecutivos y tomadores de decisión
4. Mantenga un tono profesional pero accesible

Responde SIEMPRE en {system_language}.
El resumen debe tener entre 150-250 palabras.
Sé específico con los servicios pero evita jerga técnica excesiva.
Enfócate en beneficios y resultados esperados.""",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            summary = response.choices[0].message.content

            return {
                "success": True,
                "summary": summary.strip(),
                "provider": self.provider,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "estimated_cost": self._estimate_cost(response.usage),
                },
            }

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}", exc_info=True)
            return {"success": False, "error": f"Error generating executive summary: {str(e)}"}

    def _build_executive_summary_prompt(self, request: ExecutiveSummaryRequest) -> str:
        """
        Construir prompt para generación de resumen ejecutivo

        Args:
            request: ExecutiveSummaryRequest con datos del proyecto

        Returns:
            String con el prompt completo
        """
        # Construir lista de servicios
        services_text = []
        for service in request.services:
            service_line = f"- {service.service_name}"
            if service.estimated_hours:
                service_line += f" ({service.estimated_hours} horas)"
            service_line += f": {request.currency} {service.client_price:,.2f}"
            services_text.append(service_line)

        services_list = "\n".join(services_text)

        # Construir prompt
        prompt = f"""Genera un resumen ejecutivo para la siguiente propuesta comercial:

**Proyecto:** {request.project_name}
**Cliente:** {request.client_name}
{f"**Sector:** {request.client_sector}" if request.client_sector else ""}

**Servicios Incluidos:**
{services_list}

**Inversión Total:** {request.currency} {request.total_price:,.2f}

El resumen debe:
- Presentar el proyecto de manera profesional
- Destacar el valor y beneficios de los servicios
- Ser apropiado para presentar a ejecutivos
- Tener entre 150-250 palabras
- Mantener un tono profesional pero accesible
"""

        return prompt

    async def generate_proposal_sections(
        self,
        *,
        project_name: str,
        client_name: str,
        currency: str,
        services: list[str],
        objective: str,
        timeline: str,
        payment_conditions: str,
        execution_conditions: str,
        language: str = "es",
        extra_instructions: str = "",
    ) -> dict[str, Any]:
        """
        Generate structured proposal sections with AI.
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "AI service not configured. Please set OPENAI_API_KEY in environment variables.",
            }

        try:
            system_language = "español" if language == "es" else "english"
            user_prompt = f"""Genera una propuesta comercial estructurada con la siguiente información.

Proyecto: {project_name}
Cliente: {client_name}
Moneda: {currency}
Servicios cotizados:
{chr(10).join(f"- {service}" for service in services if service.strip()) or "- (no especificados)"}

Objetivo de la propuesta:
{objective or "(no especificado)"}

Tiempo estimado de desarrollo:
{timeline or "(no especificado)"}

Condiciones de pago:
{payment_conditions or "(no especificadas)"}

Condiciones de ejecución:
{execution_conditions or "(no especificadas)"}

Instrucciones adicionales:
{extra_instructions or "(sin instrucciones adicionales)"}

Devuelve SOLO JSON válido con esta estructura:
{{
  "description": "texto",
  "objectives": ["objetivo 1", "objetivo 2", "objetivo 3"],
  "deliverables": [{{"name":"entregable 1","status":"propuesto"}}, {{"name":"entregable 2","status":"propuesto"}}],
  "scope": "texto",
  "timeline": "texto",
  "conditions": "texto",
  "free_text": "texto opcional",
  "executive_summary": "texto"
}}"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Eres experto en redacción de propuestas comerciales B2B.
Responde SIEMPRE en {system_language}.
Sé profesional, específico y accionable.
No inventes datos numéricos que no estén en el contexto; si faltan, redacta supuestos razonables.""",
                    },
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.6,
                max_tokens=1200,
            )

            content = response.choices[0].message.content
            sections = json.loads(content)
            return {
                "success": True,
                "sections": sections,
                "provider": self.provider,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "estimated_cost": self._estimate_cost(response.usage),
                },
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing proposal JSON response: {e}")
            return {"success": False, "error": "Error parsing AI response"}
        except Exception as e:
            logger.error(f"Error generating proposal sections: {e}", exc_info=True)
            return {"success": False, "error": f"Error generating proposal sections: {str(e)}"}

    async def generate_proposal_sections_with_user_key(
        self,
        *,
        user_api_key: str,
        ai_provider: str = "openai",
        project_name: str,
        client_name: str,
        currency: str,
        services: list[str],
        objective: str,
        timeline: str,
        payment_conditions: str,
        execution_conditions: str,
        language: str = "es",
        extra_instructions: str = "",
    ) -> dict[str, Any]:
        """Generate proposal sections using a user-supplied API key (OpenAI or Anthropic)."""
        system_language = "español" if language == "es" else "english"
        user_prompt = f"""Genera una propuesta comercial estructurada con la siguiente información.

Proyecto: {project_name}
Cliente: {client_name}
Moneda: {currency}
Servicios cotizados:
{chr(10).join(f"- {s}" for s in services if s.strip()) or "- (no especificados)"}

Objetivo de la propuesta:
{objective or "(no especificado)"}

Tiempo estimado de desarrollo:
{timeline or "(no especificado)"}

Condiciones de pago:
{payment_conditions or "(no especificadas)"}

Condiciones de ejecución:
{execution_conditions or "(no especificadas)"}

Instrucciones adicionales:
{extra_instructions or "(sin instrucciones adicionales)"}

Devuelve SOLO JSON válido con esta estructura:
{{
  "description": "texto",
  "objectives": ["objetivo 1", "objetivo 2", "objetivo 3"],
  "deliverables": [{{"name":"entregable 1","status":"propuesto"}}, {{"name":"entregable 2","status":"propuesto"}}],
  "scope": "texto",
  "timeline": "texto",
  "conditions": "texto",
  "free_text": "texto opcional",
  "executive_summary": "texto"
}}"""

        system_prompt = f"""Eres experto en redacción de propuestas comerciales B2B.
Responde SIEMPRE en {system_language}.
Sé profesional, específico y accionable.
No inventes datos numéricos que no estén en el contexto; si faltan, redacta supuestos razonables."""

        try:
            provider = (ai_provider or "openai").lower().strip()

            if provider == "anthropic":
                try:
                    import anthropic as anthropic_sdk

                    client = anthropic_sdk.AsyncAnthropic(api_key=user_api_key)
                    response = await client.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=1200,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}],
                    )
                    raw = response.content[0].text if response.content else "{}"
                    sections = json.loads(raw)
                    return {
                        "success": True,
                        "sections": sections,
                        "provider": "anthropic",
                        "usage": {
                            "prompt_tokens": response.usage.input_tokens,
                            "completion_tokens": response.usage.output_tokens,
                            "total_tokens": response.usage.input_tokens
                            + response.usage.output_tokens,
                            "estimated_cost": 0.0,
                        },
                    }
                except ImportError:
                    return {
                        "success": False,
                        "error": "Librería 'anthropic' no instalada en el servidor.",
                    }
            else:
                # OpenAI path with user key
                user_client = AsyncOpenAI(
                    api_key=user_api_key,
                    timeout=self.timeout_seconds,
                    max_retries=self.max_retries,
                )
                response = await user_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.6,
                    max_tokens=1200,
                )
                content = response.choices[0].message.content
                sections = json.loads(content)
                return {
                    "success": True,
                    "sections": sections,
                    "provider": "openai",
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                        "estimated_cost": self._estimate_cost(response.usage),
                    },
                }

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing user-key proposal JSON: {e}")
            return {"success": False, "error": "Error al parsear la respuesta de IA"}
        except Exception as e:
            logger.error(f"Error generating proposal with user key: {e}", exc_info=True)
            return {"success": False, "error": f"Error al generar propuesta: {str(e)}"}


# Singleton instance
ai_service = AIService()
