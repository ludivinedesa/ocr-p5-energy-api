from pydantic import BaseModel, ConfigDict, Field, field_validator


class BuildingFeatures(BaseModel):
    """
    Données attendues par le modèle.

    Les noms des champs correspondent volontairement aux variables du notebook P3
    afin que l'API reste alignée avec le pipeline entraîné.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "PrimaryPropertyType": "Hotel",
                "Neighborhood": "DOWNTOWN",
                "LargestPropertyUseType": "Hotel",
                "SecondLargestPropertyUseType": "None",
                "ThirdLargestPropertyUseType": "None",
                "YearBuilt_decade_cat": "1920s",
                "YearBuilt": 1927,
                "NumberofBuildings": 1.0,
                "NumberofFloors": 12.0,
                "PropertyGFATotal": 88434.0,
                "PropertyGFAParking": 0.0,
                "est_multi_usage": 0,
                "has_SecondLargestPropertyUseType": 0,
                "share_gfa_main": 1.0,
                "has_geo": 1,
                "log_geo_cell_150m_count": 0.6931471805599453,
                "has_gas": 1,
            }
        }
    )

    PrimaryPropertyType: str = Field(
        ...,
        description="Type principal de bâtiment.",
    )
    Neighborhood: str = Field(
        ...,
        description="Quartier du bâtiment.",
    )
    LargestPropertyUseType: str = Field(
        ...,
        description="Usage principal du bâtiment.",
    )
    SecondLargestPropertyUseType: str = Field(
        "None",
        description="Deuxième usage principal, ou None.",
    )
    ThirdLargestPropertyUseType: str = Field(
        "None",
        description="Troisième usage principal, ou None.",
    )
    YearBuilt_decade_cat: str = Field(
        ...,
        description="Décennie de construction, par exemple '1920s'.",
    )
    YearBuilt: int = Field(
        ...,
        ge=1800,
        le=2030,
        description="Année de construction.",
    )
    NumberofBuildings: float = Field(
        ...,
        ge=0,
        description="Nombre de bâtiments sur le site.",
    )
    NumberofFloors: float = Field(
        ...,
        ge=0,
        description="Nombre d'étages.",
    )
    PropertyGFATotal: float = Field(
        ...,
        gt=0,
        description="Surface totale du bâtiment.",
    )
    PropertyGFAParking: float = Field(
        0,
        ge=0,
        description="Surface de parking.",
    )
    est_multi_usage: int = Field(
        ...,
        ge=0,
        le=1,
        description="1 si bâtiment multi-usage, sinon 0.",
    )
    has_SecondLargestPropertyUseType: int = Field(
        ...,
        ge=0,
        le=1,
        description="1 si un second usage est renseigné, sinon 0.",
    )
    share_gfa_main: float = Field(
        ...,
        ge=0,
        le=1,
        description="Part de surface de l'usage principal.",
    )
    has_geo: int = Field(
        ...,
        ge=0,
        le=1,
        description="1 si coordonnées géographiques disponibles, sinon 0.",
    )
    log_geo_cell_150m_count: float = Field(
        ...,
        ge=0,
        description="Log de la densité locale sur grille 150 m.",
    )
    has_gas: int = Field(
        ...,
        ge=0,
        le=1,
        description="1 si présence de gaz, sinon 0.",
    )

    @field_validator(
        "PrimaryPropertyType",
        "Neighborhood",
        "LargestPropertyUseType",
        "SecondLargestPropertyUseType",
        "ThirdLargestPropertyUseType",
        "YearBuilt_decade_cat",
    )
    @classmethod
    def non_empty_string(cls, value: str) -> str:
        if value is None or str(value).strip() == "":
            raise ValueError("La valeur ne peut pas être vide.")
        return str(value).strip()


class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    predicted_site_energy_use_kbtu: float = Field(
        ...,
        description="Consommation énergétique prédite en kBtu/an.",
    )
    predicted_site_energy_use_gwh: float = Field(
        ...,
        description="Consommation énergétique prédite en GWh/an.",
    )
    audit_priority: str = Field(
        ...,
        description="Indication simple de priorité d'audit.",
    )
    model_type: str = Field(
        ...,
        description="Type de modèle utilisé.",
    )
    model_version: str = Field(
        ...,
        description="Version applicative du modèle.",
    )
