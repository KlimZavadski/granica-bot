"""Database interface for Supabase."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import create_client, Client
from config import settings


class Database:
    """Supabase database interface."""

    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )

    # Carriers
    async def get_carriers(self) -> List[Dict[str, Any]]:
        """Get all carriers."""
        response = self.client.table("carriers").select("*").execute()
        return response.data

    async def get_carrier_by_id(self, carrier_id: str) -> Optional[Dict[str, Any]]:
        """Get carrier by ID."""
        response = self.client.table("carriers").select("*").eq("id", carrier_id).single().execute()
        return response.data

    # Checkpoints
    async def get_mandatory_checkpoints(self) -> List[Dict[str, Any]]:
        """Get all mandatory checkpoints ordered by sequence."""
        response = (
            self.client.table("checkpoints")
            .select("*")
            .eq("type", "mandatory")
            .eq("required", True)
            .order("order_index")
            .execute()
        )
        return response.data

    async def get_checkpoint_by_id(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get checkpoint by ID."""
        response = self.client.table("checkpoints").select("*").eq("id", checkpoint_id).single().execute()
        return response.data

    # Journeys
    async def create_journey(
        self,
        user_id: int,
        carrier_id: str,
        departure_utc: datetime
    ) -> Dict[str, Any]:
        """Create a new journey."""
        data = {
            "user_id": user_id,
            "carrier_id": carrier_id,
            "departure_utc": departure_utc.isoformat(),
            "completed": False,
            "anomalous": False
        }
        response = self.client.table("journeys").insert(data).execute()
        return response.data[0]

    async def get_journey(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Get journey by ID."""
        response = self.client.table("journeys").select("*").eq("id", journey_id).single().execute()
        return response.data

    async def complete_journey(self, journey_id: str) -> Dict[str, Any]:
        """Mark journey as completed."""
        response = (
            self.client.table("journeys")
            .update({"completed": True})
            .eq("id", journey_id)
            .execute()
        )
        return response.data[0]

    async def cancel_journey(self, journey_id: str) -> Dict[str, Any]:
        """Mark journey as cancelled."""
        response = (
            self.client.table("journeys")
            .update({
                "completed": True,
                "cancelled": True,
                "notes": "Cancelled by user"
            })
            .eq("id", journey_id)
            .execute()
        )
        return response.data[0]

    async def get_user_active_journey(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's active (incomplete) journey."""
        response = (
            self.client.table("journeys")
            .select("*")
            .eq("user_id", user_id)
            .eq("completed", False)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    # Journey Events
    async def create_journey_event(
        self,
        journey_id: str,
        checkpoint_id: str,
        timestamp_utc: datetime,
        source: str = "manual",
        user_timezone: str = "Europe/Minsk",
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create a journey event (checkpoint timestamp)."""
        data = {
            "journey_id": journey_id,
            "checkpoint_id": checkpoint_id,
            "timestamp_utc": timestamp_utc.isoformat(),
            "source": source,
            "user_timezone": user_timezone,
            "lat": lat,
            "lon": lon
        }
        response = self.client.table("journey_events").insert(data).execute()
        return response.data[0]

    async def get_journey_events(self, journey_id: str) -> List[Dict[str, Any]]:
        """Get all events for a journey, ordered by timestamp."""
        response = (
            self.client.table("journey_events")
            .select("*, checkpoints(*)")
            .eq("journey_id", journey_id)
            .order("timestamp_utc")
            .execute()
        )
        return response.data

    async def get_latest_border_stats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest completed journeys with their events."""
        response = (
            self.client.table("journeys")
            .select("*, carriers(name), journey_events(*, checkpoints(name, order_index))")
            .eq("completed", True)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data


# Global database instance
db = Database()

