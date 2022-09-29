#===============================================================================
#  File-Name:	28-IDEO-NL-validation.R
#  Date:	January 20, 2019
#  Author: Andreu Casas
#  Purpose: checking the output ideo scores
#
#  Data In: 
#  - "PL-fitted-model_03.Rdata"
#  - "PL-model-input_03.csv"
#  - "PL-domains-twitter.csv"
#  - "PL-politicians-twitter.csv"
#  - "pl_domain_visits_per_user.csv"
#  Data Out:
#===============================================================================

# PACKAGES
#===============================================================================
library(Matrix)
library(mediascores)
library(dplyr)
library(ggplot2)
library(ggrepel)
library(haven)
library(rstatix)

# PATHS & CONSTANTS
#===============================================================================
data_path <- "/Users/bernhardclemm/Dropbox/Academia/EXPO/newslist/on_server/"
survey_path <- "/Users/bernhardclemm/Dropbox/Academia/EXPO/Documentation/PL/"

# DATA
#===============================================================================
# - load estimated/trained model
print(load(paste0(data_path, "PL-fitted-model_03.Rdata")))

# - load the input matrix used to estimate the model, so I can have the row 
#   and column names
Xfinal <- read.csv(paste0(data_path, "PL-model-input_03.csv"))

# - load handles for media accounts in the matrix - REVIEW THIS
media <- read.csv(paste0(data_path, "PL-domains-twitter.csv")) %>%
  mutate(twitter = gsub("@", "", .$twitter))
med_handles <- media$twitter
med_handles <- med_handles[which( # N = 174 --> 143
  as.character(med_handles) %in% as.character(colnames(Xfinal)))]

# - load handles for politician accounts in the matrix
pols <- read.csv(paste0(data_path, "PL-politicians-twitter.csv"))
pol_handles <- pols$twitter
pol_handles <- pol_handles[which( # N = 556 --> 231
  as.character(pol_handles) %in% as.character(colnames(Xfinal)))]

# MAIN
#===============================================================================
# - pull estimates for the media-politician accounts
zeta_hat <- as.data.frame(point_est(fitted_model, "zeta", prob = 0.9))

# - link the estimates to the accounts
zeta_hat$account <- colnames(Xfinal)

# - add one variable indicating whether they are politicians or media
scores <- zeta_hat %>%
  mutate(type = ifelse(account %in% as.character(pol_handles),
                       "politician", "media")) %>% 
  rename("pe" = median, "lwr" = `5%`, "upr" = `95%`,
         "twitter" = account) %>%
  mutate(twitter = as.factor(twitter)) 

# - media scores
scores_media <- scores %>% 
  filter(type == "media") %>%
  left_join(., media, by = "twitter") %>%
  mutate(group = case_when(
      pe <= quantile(pe, probs = 1/2) ~ "group1", 
      pe > quantile(pe, probs = 1/2) ~ "group2"))

scores_media_plot <- ggplot(scores_media,
       aes(x = reorder(domain, pe), 
           y = pe, ymin = lwr, ymax = upr)) +
  geom_pointrange() +
  coord_flip() +
  scale_x_discrete("") +
  scale_y_continuous("\nTwitter-based ideology score") +
  facet_wrap(~ group, scales = "free_y") +
  theme(panel.background = element_blank(),
        panel.grid.major = element_line(color = "gray80", linetype = "dotted"),
        axis.text.y = element_text(size = 6),
        strip.background = element_blank(),
        strip.text = element_blank(),
        legend.position = "bottom")

write.csv(scores_media %>% select(-type, -group),
          "PL-domains-ideo.csv")

# [ A ] POLITICIAN SCORES VALIDATION
#-------------------------------------------------------------------------------

scores_politician <- scores %>% 
  filter(type == "politician") %>%
  left_join(., pols, by = "twitter") %>%
  mutate(group = case_when(
    pe <= quantile(pe, probs = 1/3) ~ "group1", 
    pe > quantile(pe, probs = 1/3) &
      pe <= quantile(pe, probs = 2/3) ~ "group2",
    pe > quantile(pe, probs = 2/3) ~ "group3"))

scores_politician_plot <- ggplot(scores_politician,
       aes(x = reorder(name, pe), 
           y = pe, ymin = lwr, ymax = upr,
           color = party)) +
  geom_pointrange() +
  coord_flip() +
  scale_x_discrete("") +
  scale_y_continuous("\nTwitter-based ideology score") +
  # scale_color_manual()
  facet_wrap(~ group, scales = "free_y") +
  theme(panel.background = element_blank(),
        panel.grid.major = element_line(color = "gray80", linetype = "dotted"),
        axis.text.y = element_text(size = 6),
        strip.background = element_blank(),
        strip.text = element_blank(),
        legend.position = "bottom")


# [ B ] USER EXPOSURE VALIDATION
#-------------------------------------------------------------------------------

PL_domain_visits_per_user <- read.csv(
  paste0(data_path, "pl_domain_visits_per_user.csv")) %>%
  mutate(url_host = gsub("www.", "", .$url_host)) %>%
  rename("external_id" = id_txt)

PL_survey_w1 <- read_sav(paste0(survey_path, "PL_fala1_v5.sav")) %>%
  mutate(external_id = str_trim(external_id, side = c("both", "left", "right")))
PL_survey_w2 <- read_sav(paste0(survey_path, "PL_fala2_v5.sav"))
PL_survey_w3 <- read_sav(paste0(survey_path, "PL_fala3_v1.sav")) %>%
  mutate(ext_id = str_trim(ext_id, side = c("both", "left", "right")))

PL_survey_w1w2w3 <- PL_survey_w1 %>%
  left_join(., PL_survey_w2, by = "respondent_id") %>%
  left_join(., PL_survey_w3, by = "respondent_id") %>%
  mutate(ideology = scale(q2dwa_r1)) %>%
  select(respondent_id, external_id, ext_id, ideology) 

PL_survey_w1w2w3_visits <- PL_domain_visits_per_user %>%
  left_join(., PL_survey_w1w2w3, by = "external_id")

PL_visits_summary <- PL_survey_w1w2w3_visits %>%
  group_by(url_host) %>%
  get_summary_stats(ideology) %>%
  rename("domain" = url_host)

PL_ideo_scaling_visits <- PL_visits_summary %>%
  left_join(., media, by = "domain") %>%
  left_join(., scores_media, by = "twitter") %>%
  mutate(se_mediascores = (upr - pe)/1.96)

p1 <- ggplot(data = PL_ideo_scaling_visits,
       aes(x = mean, 
           y = pe)) +
  geom_point(size = 1) +
  scale_y_continuous(name = "Twitter based score") +
  scale_x_continuous(name = "Ideology of visitors score", 
                     limits = c(-1.1, 1.1)) +
  ggtitle("(A) All estimates") +
  theme_light()

p2 <- ggplot(data = PL_ideo_scaling_visits,
             aes(x = mean, 
                 y = pe)) +
  geom_point(size = 1) +
  geom_errorbar(aes(ymax = pe + se_mediascores, ymin = pe - se_mediascores)) +
  geom_errorbarh(aes(xmax = mean + se, xmin = mean - se)) +
  scale_y_continuous(name = "Twitter based score") +
  scale_x_continuous(name = "Ideology of visitors score", 
                     limits = c(-1.1, 1.1)) +
  ggtitle("(B) All estimates with CIs") +
  theme_light()

p3 <- ggplot(data = PL_ideo_scaling_visits  %>%
         filter(se < quantile(se, probs = 2/3) & 
                  se_mediascores < quantile(se_mediascores, probs = 2/3, na.rm = T)),
       aes(x = mean, 
           y = pe)) +
  geom_point(size = 1) +
  geom_errorbar(aes(ymax = pe + se_mediascores, ymin = pe - se_mediascores)) +
  geom_errorbarh(aes(xmax = mean + se, xmin = mean - se)) +
  scale_y_continuous(name = "Twitter based score") +
  scale_x_continuous(name = "Ideology of visitors score", 
                     limits = c(-1.1, 1.1)) +
  ggtitle("(C) Without tertile of least certain estimates") +
  theme_light()
  
ggarrange(p1, p2, p3, nrow = 1)


