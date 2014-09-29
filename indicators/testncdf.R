library(ncdf4)
nc<-nc_open('/Volumes/wddrive/cmip5/sea_level_above_geoid/rcp8.5/zos_Omon_FGOALS-s2_rcp85_r1i1p1_200601-210012.nc')

x<-ncvar_get(nc, "zos")
thisDims<-attributes(x)

for (itime in 1:thisDims$dim[3]) {
	image(x[,,itime], zlim=c(-1,1))
	Sys.sleep(0.1)
	}
