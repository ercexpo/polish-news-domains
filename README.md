# A list of Polish news domains with ideology scores and social media accounts

This repository contains a list of and information on 298 Polish news domains. It contains the following data sets:

- `pl-news-domains-v1.0.0.csv`: The main data set of news domains. The data set further contains a continuous variable for domain ideology (a point estimate and upper and lower confidence bounds). For coding see below.
- `pl-news-twitter-v1.0.0.csv`: The Twitter accounts linked to each domain, if available. 
- `pl-news-facebook-v1.0.0.csv`: The Facebook accounts linked to each domain, if available.

The three list can be joined to each other via the `domain` column.

## Data sources

The main list of web domains was collected from the following sources:

1. A list of Alexa's most popular 1,000 domains from 2018.
2. The most frequented domains in the trace data collected through the ERC EXPO project between May-December 2019.
3. The domains most often tweeted by US politicians at the time.

In addition, we manually searched for local news domains and added them if not yet contained in the list.

## Ideology coding

Our scaling approach builds on the `mediascores` model by Eady and Linder (https://github.com/SMAPPNYU/mediascores), which is based on the assumption of homophily: users on social media, conceived as a one-dimensional ideological space, are more likely to share news from news media accounts close to them. Instead of using sharing behavior, we use following behavior, thus assuming that users are more likely to follow news organizations close to them. 

We developed ideology scores for a subset of the list in March 2021. We only considered domains that were either visited frequently in our data, or are well-known outlets even though less visited in our data. Domains also had to have a Twitter account. This left us with 153 domains. 

To build the bipartite graph that indicates whether any user follows any news organization, we obtained the list of Twitter followers of all organizations. To avoid an overly sparse graph, we excluded organizations with less than 250 followers. To better estimate ideology scores for small media accounts, we first looked at accounts with less than 30,000 followers and got all followers who follow at least 10 of them. For the Twitter accounts with more than 30,000 followers, we pulled a random sample of 300 followers. From these following patterns, we built a matrix in which each column represents a news organization and every row a follower. A value of 1 indicates following.

The top rows and columns of the resulting matrix look like this:

```r
Xfinal[1:7, 1:7]
                    OPZZcentrala CrowdMedia_PL Kaz_Gwiazdowski RadioGlos ForbesPolska piechotapl SawickiMarek
4300044761                     0             0               0         0            0          0            0
3315916097                     0             0               0         0            0          0            0
2377558927                     0             0               0         0            0          0            1
2191944668                     0             1               0         0            0          0            0
1329587353                     0             0               0         0            0          0            0
2924616516                     0             0               0         0            1          0            1
1260648515191083008            1             0               0         1            0          0            1
``` 

We then fit the model as follows:

```r
fitted_model <- mediascores(Y = Xfinal, group = NULL,
                            variational = TRUE, user_variance = FALSE,
                            chains = 4, cores = 4, threads = 4,
                            warmup = 750, iter = 1500, seed = 1,
                            # open_progress = TRUE,
                            anchors = c(1, ncol(Xfinal)))
```

We validated the resulting scores in several ways: 
- they have good face validity according to several politics experts from Poland;
- repeating the analyses with members of parliament, most opposition politicians are on one end and most government politicians one the other end;
- comparing the ideology score of a news domain with the average user ideology visiting that domain in our browsing data, these scores correlate highly.

## If you use this resource please cite as follows:

Clemm von Hohenberg, B., Wojcieszak, M. and Casas, A. (2021). A list of Polish news domains with ideology scores and social media accounts. [DOI to add]

## Corrections and extensions

We are happy about any suggestions how to correct and extend this list.
