"""Request and response contracts for shipment-delay predictions."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    """Shipment attributes required by the trained delay-risk model."""

    model_config = ConfigDict(populate_by_name=True)

    country: Annotated[str, Field(alias="Country", min_length=1)]
    shipment_mode: Annotated[str, Field(alias="Shipment Mode", min_length=1)]
    vendor: Annotated[str, Field(alias="Vendor", min_length=1)]
    vendor_inco_term: Annotated[str, Field(alias="Vendor INCO Term", min_length=1)]
    product_group: Annotated[str, Field(alias="Product Group", min_length=1)]
    sub_classification: Annotated[str, Field(alias="Sub Classification", min_length=1)]
    dosage_form: Annotated[str, Field(alias="Dosage Form", min_length=1)]
    manufacturing_site: Annotated[str, Field(alias="Manufacturing Site", min_length=1)]
    line_item_quantity: Annotated[float, Field(alias="Line Item Quantity", ge=0)]
    unit_of_measure_per_pack: Annotated[float, Field(alias="Unit of Measure (Per Pack)", ge=0)]
    line_item_value: Annotated[float, Field(alias="Line Item Value", ge=0)]
    pack_price: Annotated[float, Field(alias="Pack Price", ge=0)]
    unit_price: Annotated[float, Field(alias="Unit Price", ge=0)]
    weight_kilograms: Annotated[float, Field(alias="Weight (Kilograms)", ge=0)]
    freight_cost_usd: Annotated[float, Field(alias="Freight Cost (USD)", ge=0)]
    line_item_insurance_usd: Annotated[float, Field(alias="Line Item Insurance (USD)", ge=0)]


class PredictionResponse(BaseModel):
    """The delay classification and confidence returned by the model."""

    delay_prediction: Annotated[int, Field(ge=0, le=1)]
    delay_probability: Annotated[float, Field(ge=0, le=1)]
    message: str
