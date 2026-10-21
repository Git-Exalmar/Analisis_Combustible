-- Tablas de resultados del modelo de actividad. Ejecutar UNA vez en la base de resultados.
IF SCHEMA_ID('ml') IS NULL EXEC('CREATE SCHEMA ml');
GO

-- Una fila por registro de telemetría puntuado (lo que lee la API del panel)
CREATE TABLE ml.ActividadEmbarcacion (
    Embarcacion     varchar(50)  NOT NULL,
    FechaRegistro   datetime2(0) NOT NULL,      -- hora de Perú, la del registro de Perú Controls
    Latitud         float        NULL,
    Longitud        float        NULL,
    Velocidad       float        NULL,
    Rpm             float        NULL,
    GalH            float        NULL,
    PuertoCercano   varchar(50)  NULL,
    DistPuertoKm    float        NULL,
    Actividad       varchar(20)  NOT NULL,      -- clase con mayor probabilidad
    Probabilidad    float        NOT NULL,      -- probabilidad de esa clase
    P_ida           float NULL, P_busqueda    float NULL, P_entrada_cala float NULL,
    P_cala          float NULL, P_salida_cala float NULL, P_retorno      float NULL,
    P_espera        float NULL, P_puerto      float NULL,
    TipoEtiqueta    varchar(12)  NOT NULL CONSTRAINT DF_Actividad_Tipo DEFAULT 'provisional',
    VersionModelo   varchar(20)  NOT NULL,
    FechaProceso    datetime2(0) NOT NULL,
    CONSTRAINT PK_ActividadEmbarcacion PRIMARY KEY (Embarcacion, FechaRegistro)
);
CREATE INDEX IX_Actividad_Fecha ON ml.ActividadEmbarcacion (FechaRegistro) INCLUDE (Actividad, Probabilidad);
GO

-- Bitácora: una fila por ejecución del proceso (para monitorear que corre y su retraso)
CREATE TABLE ml.ProcesoScoring (
    IdProceso         int IDENTITY(1,1) PRIMARY KEY,
    Inicio            datetime2(0) NOT NULL,
    Fin               datetime2(0) NULL,
    RegistrosLeidos   int NULL,
    RegistrosEscritos int NULL,
    UltimoRegistro    datetime2(0) NULL,   -- registro más reciente recibido de Perú Controls
    RetrasoMin        float NULL,          -- minutos entre ese registro y la hora del proceso
    VersionModelo     varchar(20) NULL,
    Estado            varchar(10) NOT NULL,  -- 'ok' / 'error'
    Error             nvarchar(2000) NULL
);
GO