"""Palentir OSINT - Advanced Social Media Agent.

Uses CAMEL-AI ChatAgent with social media toolkit integration.
"""

import logging
from typing import Dict, List, Any, Optional

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from toolkits.social_media_toolkit import SocialMediaToolkit


logger = logging.getLogger(__name__)


class SocialMediaIntelligenceAgent:
    """Advanced social media intelligence agent using CAMEL-AI."""

    def __init__(self):
        """Initialize social media intelligence agent."""
        # Create model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4,
        )

        # Initialize toolkit
        self.toolkit = SocialMediaToolkit()

        # Create agent
        self.agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="SocialMediaIntelligenceSpecialist",
                content=(
                    "You are a social media intelligence specialist. "
                    "Search and analyze LinkedIn, Facebook, and Instagram profiles. "
                    "Extract key information about people, companies, and connections. "
                    "Provide structured intelligence reports with findings and connections."
                ),
            ),
            model=self.model,
        )

        logger.info("Social Media Intelligence Agent initialized")

    async def investigate_person(
        self,
        name: str,
        company: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Investigate a person across social media platforms.

        Args:
            name: Person's name
            company: Optional company name

        Returns:
            Investigation results
        """
        logger.info(f"Investigating person: {name}")

        try:
            results = {
                "person": name,
                "company": company,
                "platforms": {},
                "connections": [],
                "timestamp": None,
            }

            # Search LinkedIn
            linkedin_profiles = await self.toolkit.search_linkedin_people(
                query=name,
                limit=5,
            )
            results["platforms"]["linkedin"] = [
                p.model_dump() for p in linkedin_profiles
            ]

            # Search Facebook
            facebook_profiles = await self.toolkit.search_facebook_people(
                query=name,
                limit=5,
            )
            results["platforms"]["facebook"] = [
                p.model_dump() for p in facebook_profiles
            ]

            # Search Instagram
            instagram_profiles = await self.toolkit.search_instagram_profiles(
                query=name,
                limit=5,
            )
            results["platforms"]["instagram"] = [
                p.model_dump() for p in instagram_profiles
            ]

            # Extract connections
            all_profiles = linkedin_profiles + facebook_profiles + instagram_profiles
            connections = await self.toolkit.extract_social_connections(
                [p.model_dump() for p in all_profiles]
            )
            results["connections"] = connections

            logger.info(f"Person investigation completed: {name}")
            return results

        except Exception as e:
            logger.error(f"Person investigation failed: {e}")
            return {
                "person": name,
                "status": "failed",
                "error": str(e),
            }

    async def investigate_company(
        self,
        company_name: str,
    ) -> Dict[str, Any]:
        """Investigate a company across social media platforms.

        Args:
            company_name: Company name

        Returns:
            Investigation results
        """
        logger.info(f"Investigating company: {company_name}")

        try:
            results = {
                "company": company_name,
                "platforms": {},
                "employees": [],
                "connections": [],
                "timestamp": None,
            }

            # Search LinkedIn companies
            linkedin_companies = await self.toolkit.search_linkedin_companies(
                query=company_name,
                limit=5,
            )
            results["platforms"]["linkedin_companies"] = [
                c.model_dump() for c in linkedin_companies
            ]

            # Search LinkedIn employees
            linkedin_employees = await self.toolkit.search_linkedin_people(
                query=f"{company_name} employee",
                limit=10,
            )
            results["employees"] = [
                p.model_dump() for p in linkedin_employees
            ]

            # Search Facebook pages
            facebook_pages = await self.toolkit.search_facebook_pages(
                query=company_name,
                limit=5,
            )
            results["platforms"]["facebook_pages"] = [
                p.model_dump() for p in facebook_pages
            ]

            # Search Instagram
            instagram_profiles = await self.toolkit.search_instagram_profiles(
                query=company_name,
                limit=5,
            )
            results["platforms"]["instagram"] = [
                p.model_dump() for p in instagram_profiles
            ]

            logger.info(f"Company investigation completed: {company_name}")
            return results

        except Exception as e:
            logger.error(f"Company investigation failed: {e}")
            return {
                "company": company_name,
                "status": "failed",
                "error": str(e),
            }

    async def analyze_connections(
        self,
        profiles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze connections from multiple profiles.

        Args:
            profiles: List of profiles to analyze

        Returns:
            Connection analysis
        """
        logger.info(f"Analyzing connections from {len(profiles)} profiles")

        try:
            connections = await self.toolkit.extract_social_connections(profiles)

            analysis = {
                "total_profiles": len(profiles),
                "total_connections": len(connections),
                "by_platform": {},
                "connection_summary": {},
            }

            # Group by platform
            for conn in connections:
                platform = conn.get("type", "unknown")
                if platform not in analysis["by_platform"]:
                    analysis["by_platform"][platform] = []
                analysis["by_platform"][platform].append(conn)

            # Calculate summary
            for platform, conns in analysis["by_platform"].items():
                total_connections = sum(
                    c.get("connections", 0) for c in conns
                )
                analysis["connection_summary"][platform] = {
                    "count": len(conns),
                    "total_connections": total_connections,
                    "average": total_connections // len(conns) if conns else 0,
                }

            logger.info("Connection analysis completed")
            return analysis

        except Exception as e:
            logger.error(f"Connection analysis failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }

    async def generate_intelligence_report(
        self,
        investigation_results: Dict[str, Any],
    ) -> str:
        """Generate intelligence report from investigation results.

        Args:
            investigation_results: Results from investigation

        Returns:
            Intelligence report
        """
        logger.info("Generating intelligence report")

        try:
            # Use CAMEL-AI agent to synthesize report
            user_message = BaseMessage.make_user_message(
                role_name="Analyst",
                content=(
                    f"Generate a comprehensive intelligence report from these "
                    f"social media investigation results: {investigation_results}"
                ),
            )

            response = await self.agent.step(user_message)

            report = response.msg.content if response.msg else "Report generation failed"

            logger.info("Intelligence report generated")
            return report

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return f"Error generating report: {str(e)}"

    async def identify_key_persons(
        self,
        company_name: str,
    ) -> List[Dict[str, Any]]:
        """Identify key persons in a company.

        Args:
            company_name: Company name

        Returns:
            List of key persons
        """
        logger.info(f"Identifying key persons in {company_name}")

        try:
            # Search for company employees
            employees = await self.toolkit.search_linkedin_people(
                query=f"{company_name} CEO OR founder OR executive",
                limit=10,
            )

            key_persons = [
                {
                    "name": e.name,
                    "headline": e.headline,
                    "company": e.company,
                    "connections": e.connections,
                    "profile_url": e.profile_url,
                }
                for e in employees
            ]

            logger.info(f"Found {len(key_persons)} key persons")
            return key_persons

        except Exception as e:
            logger.error(f"Key person identification failed: {e}")
            return []
