#===============================================================================
#  File-Name:	PL-twitter-mediascore-model.R
#  Date:	April 14 2021
#  Author: Andreu Casas / Bernhard Clemm
#  Purpose: to build ideology scores for PL domains
#
#  Data In: 
#  # Objects to recreate Sparse Matrix - several different configurations have been tried:
#  - PL-indices-3.txt
#  - PL-pointers-3.txt
#  - PL-graph/PL-values-3.txt
#  - PL-graph/PL-rownames-3.txt
#  - PL-graph/PL-colnames-3.txt
# # The handles for the media and politician accounts
#  - PL-domains-twitter.csv
#  - PL-politicians-twitter.csv
#
#  Data Out:
#  - PL-model-input_01.csv
#  - PL-fitted_model_01.Rdata 

#===============================================================================

# PACKAGES
#===============================================================================
library(Matrix)
library(mediascores)

# PATHS & CONSTANTS
#===============================================================================
data_path <- "/Users/bernhardclemm/Dropbox/Mac/Documents/Academia/EXPO/ideology_scaling_server/twitter-ideo/PL/"

# DATA 
#===============================================================================
# - load sparse matrix
ind <- scan(paste0(data_path, "PL-graph/PL-indices-3.txt"))
pointers <- scan(paste0(data_path, "PL-graph/PL-pointers-3.txt"))
values <- scan(paste0(data_path, "PL-graph/PL-values-3.txt"))
rnames <- read.table(paste0(data_path, "PL-graph/PL-rownames-3.txt"),
                     colClasses = "character")
cnames <- read.table(paste0(data_path, "PL-graph/PL-colnames-3.txt"), 
                     colClasses = "character")
X <- sparseMatrix(j=ind, p=pointers, x=values,
                  dims=c(nrow(rnames), nrow(cnames)), index1=FALSE)
X <- as.matrix(X)
rownames(X) <- rnames[,1]
colnames(X) <- cnames[,1]

# - load handles for media accounts in the matrix
media <- read.csv(paste0(data_path, "PL-domains-twitter.csv"))
med_handles <- gsub("@", "", media$twitter)
med_handles <- med_handles[which( # N = 174 --> 135
  as.character(med_handles) %in% as.character(colnames(X)))]

# - load handles for politician accounts in the matrix
pols <- read.csv(paste0(data_path, "PL-politicians-twitter.csv"))
pol_handles <- gsub("@", "", pols$twitter)
pol_handles <- pol_handles[which( # N = 556 --> 241
  as.character(pol_handles) %in% as.character(colnames(X)))]
pol_handles <- unique(pol_handles)

# DATA WRANGLING
#===============================================================================
# The matrix is currently 18276 x 377
# First model with all elites

Z <- as.data.frame(X)

# For alternative models: get rid of some elites
# - get rid of the columns for politicians with not that many followers in the
#   graph
# Zpol <- Z[,as.character(pol_handles)] 
# pol_finalcols <- colnames(Zpol)[which(colSums(Zpol) > 225)] 
# - get rid of the columns for media accounts with very few followers 
# med_handlespresent <- med_handles[which(
#   as.character(med_handles) %in% colnames(Z))]
# Zmed <- Z[,as.character(med_handlespresent)] 
# med_finalcols <- colnames(Zmed)[which(colSums(Zmed) > 30)] 
# - a version of the matrix only with these columns
# Z02 <- Z[,c(as.character(med_finalcols), 
#             as.character(pol_finalcols))] # (18276 x 278)

Z02 <- Z

# - now getting rid of the follower nodes with very few edges
finalrows <- rownames(Z02)[(which(rowSums(Z02) > 50))]
Z03 <- Z02[finalrows,] # 5362 x 377

Xfinal <- Z03
write.csv(Z03, paste0(data_path, "PL-model-input_03.csv"), row.names = FALSE)

# MAIN
#===============================================================================
# - fitting the model
fitted_model <- mediascores(Y = Xfinal, group = NULL,
                            variational = TRUE, user_variance = FALSE,
                            chains = 4, cores = 4, threads = 4,
                            warmup = 750, iter = 1500, seed = 1,
                            # open_progress = TRUE,
                            anchors = c(1, ncol(Xfinal)))
# OUTPUT
#===============================================================================
save(fitted_model, file = paste0(data_path, "PL-fitted-model_03.RData"))
