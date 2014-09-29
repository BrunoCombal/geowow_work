# \author Bruno Combal
# \date January 2013
# \brief read a ncdf file, computes seasonality, saves it to a file

library(ncdf4)
nc<-nc_open('/Volumes/wddrive/cmip5/sea_level_above_geoid/rcp8.5/zos_Omon_FGOALS-s2_rcp85_r1i1p1_200601-210012.nc')

data<-ncvar_get(nc, "zos")
thisDims<-attributes(data)
nodataIn=1.e20
nodataOut=0
minVal<-array(0.0, dim=c(thisDims$dim[1], thisDims$dim[2]))
maxVal<-array(0.0, dim=c(thisDims$dim[1], thisDims$dim[2]))

for (xx in 1:thisDims$dim[1]) {
	for (yy in 1:thisDims$dim[2]) {
		if (data[xx,yy,1] < nodataIn) {
			tseries <- ts( data[xx,yy,], frequency=12, start=c(2006,1) )
			tsdecompose<-decompose(tseries)
			minVal[xx,yy] <- min(tsdecompose$seasonal)
			maxVal[xx,yy] <- max(tsdecompose$seasonal)
		} 
		}
	}

image(minVal)
#for (itime in 1:thisDims$dim[3]) {
#	image(x[,,itime], zlim=c(-1,1))
#	Sys.sleep(0.1)
#	}
