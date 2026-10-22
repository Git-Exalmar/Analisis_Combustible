-- Faenas de embarcaciones propias desde 2025: una fila por faena.
-- Las calas van aparte (calas.sql); se unen en Python por IdFaena.
SELECT
    pd.IdFaena, pd.NumeroFaenas, pd.IND_IdEmbarcacion, e.Embarcacion, pd.Matricula, pd.EstadoFaena,
    pd.PuertoZarpe, pd.FechaHoraZarpe,
    pd.NumeroCalas, pd.FechaHoraPrimeraCala, pd.FechaHoraUltimaCala,
    pd.FechaHoraArriboEstimado, pd.FechaHoraArriboReal,
    pd.FechaHoraInicioDescarga, pd.FechaHoraFinDescarga, pd.HorasDescarga
FROM BD_DWH_SILVER.FAENAS.[Fact_Faenas]  pd
INNER JOIN BD_DWH_SILVER.FAENAS.Dim_Embarcacion  e ON pd.IND_IdEmbarcacion = e.IdEmbarcacion
WHERE pd.FechaHoraZarpe >= '2025-01-01'
  AND e.EsPropio = 1;