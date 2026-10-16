SET NOCOUNT ON; 
SELECT 
    m.id, 
    e.Embarcacion AS ep, 
    m.fecha, 
    TRY_CAST(m.Latitude AS float) AS Latitud, 
    TRY_CAST(m.Longitude AS float) AS Longitud, 
    TRY_CAST(m.Speed AS float) / 10.0 AS Velocidad, 
    m.header AS Rumbo, 
    TRY_CAST(m.parameter12 AS float) / 3.785 AS gal_h, -- factor de conversión
    TRY_CAST(m.parameter02 AS float) AS rpm 
    FROM 
        [dbo].[MP_E_H] m 
    INNER JOIN 
        [dbo].[Embarcacion] e ON m.IdEmbarcacion = e.IdEmbarcacion 
    WHERE 
        m.parameter02 <> '0' AND m.parameter12 <> '0';





