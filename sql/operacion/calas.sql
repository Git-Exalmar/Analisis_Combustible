-- Calas de esas faenas: una fila por cala.
-- FechaHoraCala = hora registrada, que en la práctica es el FIN de la cala.
SELECT c.IdFaena, c.FechaHoraCala
FROM BD_DWH_SILVER.FAENAS.[Calas] c
WHERE c.IdFaena IN (
    SELECT pd.IdFaena
    FROM BD_DWH_SILVER.FAENAS.[Fact_Faenas] pd
    INNER JOIN BD_DWH_SILVER.FAENAS.Dim_Embarcacion e ON pd.IND_IdEmbarcacion = e.IdEmbarcacion
    WHERE pd.FechaHoraZarpe >= '2025-01-01'
      AND e.EsPropio = 1
);