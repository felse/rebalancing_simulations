# use install.packages()
library(ggplot2)
library(reshape)
library(RColorBrewer)
library(Rmisc)
library(readr) #more detailed read_csv()
library(rstudioapi)

current_path <- getActiveDocumentContext()$path 
setwd(dirname(current_path ))

simulation_file = "step_5_osds_32_caps_355-466_bws_600-150_split_sizes_all_geq_1_0.7_reps_1000"

options(scipen=10000000)

df <- read_csv(paste(simulation_file, ".csv", sep=""),
               col_types = cols(X1 = col_skip(),
                                initial_distribution_type = col_factor(levels = c("lpt", "totrand", "rand_r_r", "caprand")),
                                rebalancing_mechanism = col_character(), 
                                improvement_ratio_percent = col_double(),
                                rebalanced_makespan = col_double(),
                                initial_makespan = col_double(),
                                total_size_moved = col_double() ))

# convert measured values into some reasonable units
# absolute makespans into minutes (from seconds/1024 mb)
df$rebalanced_makespan = (1024/60) * df$rebalanced_makespan
df$initial_makespan = (1024/60) * df$initial_makespan
# total size moved into TB (from KB)
df$total_size_moved = (1/ (1024 * 1024 * 1024)) * df$total_size_moved

# initial_distribution_type caprand is the only one that makes sense: 
# otherwise, OSDs have more data than their capacity
df = subset(df, initial_distribution_type == "caprand")

color_theme = c('#ffff99', '#8dd3c7', '#4daf4a', '#1f78b4')

### plot absolute makespan values

df_sum_shan = Rmisc::summarySE(df, "rebalanced_makespan", groupvars=c("initial_distribution_type", "rebalancing_mechanism"))

# add one row with the initial makespan to df_sum_shan for display in plot
summary_initial_ms = Rmisc::summarySE(df, "initial_makespan", groupvars=c("initial_distribution_type", "rebalancing_mechanism"))
summary_initial_ms$rebalancing_mechanism = "random"
df_sum_shan[nrow(df_sum_shan) + 1, ] = summary_initial_ms[1, ]

print("rebalanced makespans:")
print(df_sum_shan$rebalancing_mechanism)
print(round(df_sum_shan$rebalanced_makespan, digits = 2))

output_pdf = paste("pdfs/", simulation_file, "_absolute_makespans.pdf", sep="")
pdf(output_pdf, width=11, height=5, title="makespans")

makespan_plot=ggplot(data=df_sum_shan,aes(x=rebalancing_mechanism, y=rebalanced_makespan, fill=rebalancing_mechanism)) + 
  geom_hline(yintercept = seq(0, 3, 0.2), color = "grey") +
  geom_bar(stat="identity", position=position_dodge(), colour="black")+
  theme_classic()+
  geom_errorbar(aes(ymin=rebalanced_makespan-sd, ymax=rebalanced_makespan+sd), width=.2,position=position_dodge(.9))+
  labs(y = "Makespan", x = "Rebalancing algorithm")+
  scale_y_continuous() +
  theme(axis.text.y=element_blank()) +
  scale_x_discrete(limit = c("random", "optimal", 
                             "lpt_mean0.9", "lpt_mean0.95", "lpt_mean1.0", "lpt_mean1.05", "lpt_mean1.1", #"lpt_mean1.2", 
                             "two_step_optimal", "move_one"), 
                   labels = c("Random", "Lower\n Bound",  
                              "LPT 0.90", "LPT 0.95", "LPT 1.00", "LPT 1.05", "LPT 1.10", #"LPT 1.20", 
                              "Oblivious", "Local")) +
  theme(axis.text.x=element_text(angle = 60, vjust = 0.5)) +
  theme(legend.position="none")+
  theme(legend.text = element_text(size=20), legend.title = element_text(size=20))+
  theme(legend.title=element_blank())+
  theme(axis.title = element_text(size=24),axis.text=element_text(size=24)) +
  guides(fill=guide_legend(ncol=2))
plot(makespan_plot)
dev.off()
embedFonts(output_pdf)